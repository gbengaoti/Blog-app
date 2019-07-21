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

# test that guest can access the home page
query = "index"
status_code = 200
passed_msg = "Test 1 PASSED - Guest user can access home page"
run_test(query, status_code, passed_msg)

# test that guest can view all users
query = "users"
status_code = 200
passed_msg = "Test 2 PASSED - Guest user can access view users"
run_test(query, status_code, passed_msg)

# test that guest can view articles for existing user
query = "users/1"
status_code = 200
passed_msg = "Test 3 PASSED - Guest user can access user articles"
run_test(query, status_code, passed_msg)

# test that guest cannot view articles for non existing user
query = "users/0"
status_code = 404
passed_msg = "Test 4 PASSED - Guest user cannot access user articles for nonexisting user"
run_test(query, status_code, passed_msg)

# test that guest can view article
query = "user/1/article/1/view"
status_code = 200
passed_msg = "Test 5 PASSED - Guest user can view user article"
run_test(query, status_code, passed_msg)

# test that guest cannot view non existing user and existing article
query = "user/0/article/1/view"
status_code = 404
passed_msg = "Test 6 PASSED - Guest user cannot view user article for nonexisting user"
run_test(query, status_code, passed_msg)

# test that guest cannot view existing user and non existing article
query = "user/1/article/0/view"
status_code = 404
passed_msg = "Test 7 PASSED - Guest user cannot view nonexisting article for existing user"
run_test(query, status_code, passed_msg)

# test that guest cannot add article
query = "user/1/article/new"
status_code = 200
expected_page = "http://localhost:5000/users/1"
passed_msg = "Test 8 PASSED - Guest user cannot view page to add article"
run_test_pages(query, expected_page, passed_msg, status_code)

# adding article for invalid user as guest
query = "user/0/article/new"
status_code = 404
passed_msg = "Test 9 PASSED - Guest user cannot view page to add article for invalid user"
run_test(query, status_code, passed_msg)

# test that guest cannot edit article
query = "user/1/article/1/edit"
status_code = 200
expected_page = "http://localhost:5000/users/1"
passed_msg = "Test 10 PASSED - Guest user cannot view page to edit article"
run_test_pages(query, expected_page, passed_msg, status_code)

# editing article for invalid user as guest
query = "user/0/article/1/edit"
status_code = 404
passed_msg = "Test 11 PASSED - Guest user cannot view page to edit article for invalid user"
run_test(query, status_code, passed_msg)

# test that guest cannot delete article
query = "user/1/article/1/delete"
status_code = 200
expected_page = "http://localhost:5000/users/1"
passed_msg = "Test 12 PASSED - Guest user cannot view page to delete article"
run_test_pages(query, expected_page, passed_msg, status_code)

# deleting article for invalid user as guest
query = "user/0/article/1/delete"
status_code = 404
passed_msg = "Test 13 PASSED - Guest user cannot view page to delete article for invalid user"
run_test(query, status_code, passed_msg)

#### JSON tests #####

# get comments in JSON format for article
query = "user/1/article/1/comments/JSON"
status_code = 200
passed_msg = "Test 14 PASSED - Guest user can get comments JSON"
run_test_json(query, status_code, passed_msg)

# if user enters invalid url
query = "user/0/article/1/comments/JSON"
status_code = 200
passed_msg = "Test 15 PASSED - Guest user can get comments JSON"
run_test_json(query, status_code, passed_msg)

# if user enters invalid url
query = "user/1/article/0/comments/JSON"
status_code = 200
passed_msg = "Test 16 PASSED - Guest user can get comments JSON"
run_test_json(query, status_code, passed_msg)


# get articles for user
query = "user/1/articles/JSON"
status_code = 200
passed_msg = "Test 17 PASSED - Guest user can get articles JSON"
run_test_json(query, status_code, passed_msg)

query = "user/0/articles/JSON"
status_code = 200
passed_msg = "Test 18 PASSED - Guest user can get articles JSON"
run_test_json(query, status_code, passed_msg)

query = "user/1/article/1/JSON"
status_code = 200
passed_msg = "Test 19 PASSED - Guest user can get article JSON"
run_test_json(query, status_code, passed_msg)


query = "user/0/article/1/JSON"
status_code = 200
passed_msg = "Test 20 PASSED - Guest user can get article JSON"
run_test_json(query, status_code, passed_msg)

query = "user/1/article/0/JSON"
status_code = 200
passed_msg = "Test 21 PASSED - Guest user can get article JSON"
run_test_json(query, status_code, passed_msg)

query = "users/JSON"
status_code = 200
passed_msg = "Test 22 PASSED - Guest user can get users JSON"
run_test_json(query, status_code, passed_msg)