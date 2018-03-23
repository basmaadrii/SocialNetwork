from flask import Flask, jsonify, request, abort
from flaskext.mysql import MySQL
from facebook import GraphAPI
import pagination


#initialize Flask app#  MySQL Database
app = Flask(__name__)
app.debug = True
mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'SocialNetwork'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)
conn = mysql.connect()
cursor = conn.cursor()

# initialize Graph API Access Token (must be changed for each user)
token = 'EAAIzpxUzyoMBAC2rq6ZBvm6h9e0sE8O780Qum2yI8RtgpHkvk0igcayXM8NTa42BFbiFCLdjCCSjCZAckKBjgOwyVpE5eYXlW3CryHY1IGeYL3oQB6XSy6mB3tfGSWYx936DJwPF7KRpf64CJrRfzaiAjYmD941gksbxZAtg7UGf4WoTBOp9r3rQ3vK9SXhU7bHpumuSPSO6l3beXYZCziZAubrWKZAWUrsVyax5xH2pPkEjLKztzV'
graph = GraphAPI(access_token=token)


@app.route('/users/<facebookID>', methods=['GET'])
def get_user(facebookID):
    # get query param ?local
    local = request.args.get('local')

    if local:
        # fetch data of id = facebookID
        query = "SELECT * FROM users WHERE user_id = " + str(facebookID)
        cursor.execute(query)
        data = cursor.fetchall()

        if len(data) is 0:
            return "User doesn't exist!"
        else:
            return jsonify(data)

    # request data of user
    user_data = graph.request('/' + str(facebookID))
    cursor.callproc('sp_createUser', (user_data['id'], user_data['name']))

    data = cursor.fetchall()

    if len(data) is 0:  # if user doesn't exists add new record in database
        conn.commit()
        return jsonify(user_data)

    else:               # if user exists update his record if needed
        query = "SELECT user_name FROM users WHERE user_id = " + str(user_data['id'])
        cursor.execute(query)
        data = cursor.fetchall()

        if user_data['name'] != str(data[0]):
            query = "UPDATE users SET user_name = '" + str(user_data['name']) + "' WHERE user_id = " + str(user_data['id'])
            cursor.execute(query)
            data = cursor.fetchall()

            if len(data) is 0:
                conn.commit()
                return jsonify(user_data)
            else:
                return "err: " + str(data[0])


@app.route('/users/<facebookID>/posts', defaults={'page' : 1}, methods=['GET'])
@app.route('/users/<facebookID>/posts/page/<int:page>', methods=['GET'])
def get_posts(facebookID, page):
    page_content = {}
    # get query param ?local
    local = request.args.get('local')

    # load data from database if exists
    if local:
        query = "SELECT * FROM posts WHERE user_id = " + str(facebookID)
        cursor.execute(query)
        data = cursor.fetchall()

        if len(data) is 0:
            return "You don't have any posts yet!"
        else:
            return jsonify(data)

    # request user's posts
    user_posts = graph.request('/' + str(facebookID) + '/posts?limit=25')
    posts = user_posts['data']

    query = "SELECT * FROM posts WHERE user_id = " + str(facebookID) + " ORDER BY created_time DESC"
    cursor.execute(query)
    data = cursor.fetchall()

    if len(data) is 0:
        for post in posts:
            cursor.callproc('sp_createPost', (post['id'], facebookID, post['message'], post['created_time']))
            data = cursor.fetchall()
            if len(data) is 0:
                conn.commit()

    else:
        i = 0

        for i in range(0, len(posts)):
            # compare last entry with each post in fetched posts
            if data[0][0] == posts[i]['id']:
                break

            # if last post in database is not reached yet, add post[i]
            cursor.callproc('sp_createPost', (posts[i]['id'], facebookID, posts[i]['message'], posts[i]['created_time']))
            d = cursor.fetchall()
            if len(d) is 0:
                conn.commit()

        # delete outdated posts
        if i > 0:
            count = len(data) + i
            for i in range(0, count - 25):
                query = "DELETE FROM posts WHERE post_id = '" + str(data[len(data) - (i + 1)][0]) + "'"
                cursor.execute(query)
                conn.commit()



    query = "SELECT * FROM posts WHERE user_id = '" + facebookID + "' ORDER BY created_time DESC"
    cursor.execute(query)
    row_headers = [x[0] for x in cursor.description]
    data = cursor.fetchall()
    json_data = []
    for entry in data:
        json_data.append(dict(zip(row_headers, entry)))
    count = len(data)

    pg = pagination.Pagination(count, page)
    offset = (page - 1) * pg.page_size
    page_content['data'] = json_data[offset + 1: offset + pg.page_size + 1]

    if not page_content['data']:
        abort(404)

    page_content['offset'] = offset
    page_content['total'] = count
    page_content['page'] = page

    if pg.has_next():
        page_content['next'] = str(request.url_root) + 'users/' + facebookID + '/posts/page/' + str(page + 1)
    if pg.has_previous():
        page_content['previous'] = str(request.url_root) + 'users/' + facebookID + '/posts/page/' + str(page - 1)

    return jsonify(page_content)


@app.route('/users/', defaults={'page' : 1})
@app.route('/users/page/<int:page>', methods=['GET'])
def get_users(page):
    page_content = {}
    query = "SELECT * FROM users"
    cursor.execute(query)
    row_headers = [x[0] for x in cursor.description]
    data = cursor.fetchall()
    json_data = []
    for entry in data:
        json_data.append(dict(zip(row_headers, entry)))
    count = len(data)

    if count == 0:
        'No Users Found!'
    else:
        pg = pagination.Pagination(count, page)
        offset = (page - 1) * pg.page_size
        page_content['data'] = json_data[offset + 1 : offset + pg.page_size + 1]
        if not page_content['data']:
            abort(404)
        page_content['offset'] = offset
        page_content['total'] = count
        page_content['page'] = page
        if pg.has_next():
            page_content['next'] = str(request.url_root) + 'users/page/' + str(page + 1)
        if pg.has_previous():
            page_content['previous'] = str(request.url_root) + 'users/page/' + str(page - 1)
        return jsonify(page_content)


if __name__ == '__main__':
    app.run()
