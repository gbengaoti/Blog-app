## This tests assumes user is signed in as User with id - 1 
import requests, random

base_uri = "http://localhost:5000/"

def run_test(query, status_code, passed_msg):
    # test that guest can access the home page
    uri =  base_uri + query
    print("Sending query for:", uri)
    try:
      r = requests.get(uri)
      if r.status_code != status_code:
        print("The server returned status code {} "
              "instead of a {}.".format(r.status_code, status_code))
      else:
        print(passed_msg)
    except requests.ConnectionError:
      print("Couldn't connect to the server. Is it running on port 5000?")
    except requests.RequestException as e:
      print("Couldn't communicate with the server ({})".format(e))
      print("If it's running, take a look at the server's output.")

def run_test_pages(query, expected_page, passed_msg, status_code):
    # test that guest can access the home page
    uri =  base_uri + query
    print("Sending query for:", uri)
    try:
      r = requests.get(uri)
      if r.status_code != status_code:
        print("The server returned status code {} "
              "instead of a {}.".format(r.status_code, status_code))
      else:
        if r.url == expected_page:
            print(passed_msg)
        else:
            print("Test Failed - Don't know where you are!")
    except requests.ConnectionError:
      print("Couldn't connect to the server. Is it running on port 5000?")
    except requests.RequestException as e:
      print("Couldn't communicate with the server ({})".format(e))
      print("If it's running, take a look at the server's output.")

def run_test_json(query, status_code, passed_msg):
    # test that guest can access the home page
    uri =  base_uri + query
    print("Sending query for:", uri)
    try:
      r = requests.get(uri)
      if r.status_code != status_code:
        print("The server returned status code {} "
              "instead of a {}.".format(r.status_code, status_code))
      else:
        try:
            responses = r.json()
            print(passed_msg)
        except ValueError:
            print("Test Failed - Don't know where you are!")
    except requests.ConnectionError:
      print("Couldn't connect to the server. Is it running on port 5000?")
    except requests.RequestException as e:
      print("Couldn't communicate with the server ({})".format(e))
      print("If it's running, take a look at the server's output.")

# user can view users
query = "users"
status_code = 200
passed_msg = "Test 1 PASSED - signed in user can access view users"
run_test(query, status_code, passed_msg)

# user can view articles for self and others
query = "users/1"
status_code = 200
passed_msg = "Test 2 PASSED - signed in user can access view own articles"
run_test(query, status_code, passed_msg)

query = "users/2"
status_code = 200
passed_msg = "Test 3 PASSED - signed in user can access view other articles"
run_test(query, status_code, passed_msg)

# user can view own article
query = "user/1/article/1/view"
status_code = 200
passed_msg = "Test 4 PASSED - signed in user can access view particular article"
run_test(query, status_code, passed_msg)

# user can view other article(non existing)
query = "user/2/article/1/view"
status_code = 404
passed_msg = "Test 5 PASSED - signed in user cannot access non-existing article"
run_test(query, status_code, passed_msg)

# user can view other article(non existing)
query = "user/3/article/3/view"
status_code = 200
passed_msg = "Test 6 PASSED - signed in user can access view others article"
run_test(query, status_code, passed_msg)

# user can edit own article
query = "user/1/article/1/edit"
status_code = 200
passed_msg = "Test 7 PASSED - signed in user can access edit own article"
run_test(query, status_code, passed_msg)


# user cannot edit other user article
query = "user/3/article/3/edit"
expected_page = "http://localhost:5000/users/3"
status_code = 200
passed_msg = "Test 8 PASSED - signed in user cannot edit others article"
run_test_pages(query, expected_page, passed_msg, status_code)

# user can add article
query = "user/1/article/new"
status_code = 200
passed_msg = "Test 9 PASSED - signed in user can add new article"
run_test(query, status_code, passed_msg)

# user cannot add article for another user
query = "user/2/article/new"
expected_page = "http://localhost:5000/users/2"
status_code = 200
passed_msg = "Test 10 PASSED - signed in user cannot add article for another user"
run_test_pages(query, expected_page, passed_msg, status_code)

# user can delete own article
query = "user/1/article/1/delete"
status_code = 200
passed_msg = "Test 11 PASSED - signed in user can delete own article"
run_test(query, status_code, passed_msg)

# user cannot delete article for another user
query = "user/3/article/3/delete"
expected_page = "http://localhost:5000/users/3"
status_code = 200
passed_msg = "Test 12 PASSED - signed in user cannot delete article for another user"
run_test_pages(query, expected_page, passed_msg, status_code)


# user can get JSON files like guest
# get articles for user
query = "user/1/articles/JSON"
status_code = 200
passed_msg = "Test 13 PASSED - user can get articles JSON"
run_test_json(query, status_code, passed_msg)

query = "user/3/articles/JSON"
status_code = 200
passed_msg = "Test 14 PASSED - user can get other articles JSON"
run_test_json(query, status_code, passed_msg)

query = "user/1/article/1/JSON"
status_code = 200
passed_msg = "Test 15 PASSED - user can get article JSON"
run_test_json(query, status_code, passed_msg)


query = "user/3/article/1/JSON"
status_code = 200
passed_msg = "Test 16 PASSED - user can get other article(non-existing) JSON"
run_test_json(query, status_code, passed_msg)

query = "user/1/article/0/JSON"
status_code = 200
passed_msg = "Test 17 PASSED - user can get article JSON"
run_test_json(query, status_code, passed_msg)

query = "users/JSON"
status_code = 200
passed_msg = "Test 18 PASSED - user can get users JSON"
run_test_json(query, status_code, passed_msg)


