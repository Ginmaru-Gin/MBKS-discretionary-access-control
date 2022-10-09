from database import Database

db = Database('test.db', 'create_db.sql')

db.add_user('user1', 'pass1','/home/user1')
db.add_user('user2', 'pass2', '/home/user2')

db.add_group('group1')
db.add_group('group2')

db.add_user_to_group('user1', 'group1')
db.add_user_to_group('user1', 'group2')
db.add_user_to_group('user2', 'group2')

db.add_file('/home/user1/file1')
db.add_file('/home/user1/file2')
db.add_file('/home/user2/file1')

db.set_user_rights('user1', '/home/user1/file1', 1)
db.set_user_rights('user1', '/home/user1/file2', 1)
db.set_user_rights('user2', '/home/user2/file1', 1)
db.set_user_rights('user2', '/home/user1/file1', 1)
db.set_group_rights('group2', '/home/user2/file1', 1)
db.set_user_rights('user1', '/home/user1/file1', 0)

# db.del_file('/home/user1/file1')
# db.del_user_from_group('user2', 'group2')

# db.del_user('user1')
# db.del_user('user2')
# db.del_group('group1')
# db.del_group('group2')
