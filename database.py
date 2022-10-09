import os
import sqlite3


class Database:
    __connection: sqlite3.Connection
    __cursor: sqlite3.Cursor

    def __init__(self, db_filename: str, init_sql_script_filename: str):
        self.__connection = sqlite3.connect(db_filename)
        self.__connection.execute("PRAGMA foreign_keys = ON")
        self.__cursor = self.__connection.cursor()
        with open(init_sql_script_filename) as script:
            self.__cursor.executescript(script.read())
        self.__connection.commit()

    def __del__(self):
        self.__connection.close()

    def __write_transactional(req):
        def wrapper(self_ref, *args):
            try:
                self_ref.__request('BEGIN IMMEDIATE TRANSACTION')
                result = req(self_ref, *args)
                self_ref.__commit()
                return result
            except Exception as exc:
                self_ref.__rollback()
                raise exc

        return wrapper

    def __read_transactional(req):
        def wrapper(self_ref, *args):
            try:
                self_ref.__request('BEGIN DEFERRED TRANSACTION')
                result = req(self_ref, *args)
                self_ref.__commit()
                return result
            except Exception as exc:
                self_ref.__rollback()
                raise exc

        return wrapper

    def __request(self, sql_req: str, args=None):
        if args is None:
            args = {}
        return self.__cursor.execute(sql_req, args)

    def __commit(self):
        self.__connection.commit()

    def __rollback(self):
        self.__connection.rollback()

    @__write_transactional
    def add_user(self, name: str, passwd: str, home_dir: str):
        self.__request("INSERT INTO subjects DEFAULT VALUES")
        sql = """INSERT INTO users(id, name, password, home_dir)
        VALUES ((SELECT seq FROM sqlite_sequence WHERE name IS 'subjects'),:name, :passwd, :home_dir)"""
        args = {'name': name, 'passwd': passwd, 'home_dir': home_dir}
        return self.__request(sql, args)

    @__write_transactional
    def del_user(self, name: str):
        req = """DELETE FROM subjects WHERE id IS (SELECT id FROM users WHERE name IS :name)"""
        args = {'name': name}
        return self.__request(req, args)

    @__write_transactional
    def add_group(self, name: str):
        self.__request("INSERT INTO subjects DEFAULT VALUES")
        req = """INSERT INTO groups(id, name)
        VALUES ((SELECT seq FROM sqlite_sequence WHERE name IS 'subjects'),:name)"""
        args = {'name': name}
        return self.__request(req, args)

    @__write_transactional
    def del_group(self, name: str):
        req = """DELETE FROM subjects WHERE id IS (SELECT id FROM groups WHERE name IS :name)"""
        args = {'name': name}
        return self.__request(req, args)

    @__write_transactional
    def add_user_to_group(self, user: str, group: str):
        req = """INSERT INTO user_has_group(user_id, group_id)
        VALUES ((SELECT id FROM users WHERE name IS :user),(SELECT id from groups WHERE name IS :group))"""
        args = {'user': user, 'group': group}
        return self.__request(req, args)

    @__write_transactional
    def del_user_from_group(self, user: str, group: str):
        req = """DELETE FROM user_has_group WHERE
        user_id IS (SELECT id FROM users WHERE name IS :user) AND
        group_id IS (SELECT id FROM groups WHERE name IS :group)"""
        args = {'user': user, 'group': group}
        return self.__request(req, args)

    @__write_transactional
    def add_file(self, path: str):
        directory, filename = os.path.split(path)
        req = """INSERT INTO files(path, name)
        VALUES (:directory, :filename)"""
        args = {'directory': directory, 'filename': filename}
        return self.__request(req, args)

    @__write_transactional
    def del_file(self, path: str):
        directory, filename = os.path.split(path)
        req = """DELETE FROM files WHERE path IS :directory AND name IS :filename"""
        args = {'directory': directory, 'filename': filename}
        return self.__request(req, args)

    @__write_transactional
    def set_user_rights(self, user: str, path: str, rights: int):
        path, filename = os.path.split(path)
        req = """INSERT INTO subject_has_file(subject_id, file_id, rights)
        VALUES ((SELECT id FROM users WHERE name IS :user),
        (SELECT id FROM files WHERE path IS :path AND name IS :filename),
        :rights)
        ON CONFLICT DO UPDATE SET rights=:rights"""
        args = {'user': user, 'path': path, 'filename': filename, 'rights': rights}
        return self.__request(req, args)

    @__write_transactional
    def set_group_rights(self, group: str, path: str, rights: int):
        path, filename = os.path.split(path)
        req = """INSERT INTO subject_has_file(subject_id, file_id, rights)
        VALUES ((SELECT id FROM groups WHERE name IS :group),
        (SELECT id FROM files WHERE path IS :path AND name IS :filename),
        :rights)"""
        args = {'group': group, 'path': path, 'filename': filename, 'rights': rights}
        return self.__request(req, args)

    @__read_transactional
    def get_group_rights(self, group: str, path: str) -> int:
        path, filename = os.path.split(path)
        req = """SELECT subjects.id AS subject_id, rights
        FROM (SELECT id FROM groups
            WHERE name IS :group) AS subjects
        LEFT JOIN (SELECT shf.subject_id, shf.rights
            FROM files AS f
            JOIN subject_has_file shf
            ON f.id IS shf.file_id AND f.path IS :path AND f.name IS :filename) AS shf
        ON shf.subject_id IS subjects.id"""
        args = {'group': group, 'path': path, 'filename': filename}
        rights = self.__request(req, args).fetchone()[1]
        if rights is None:
            rights = 0
        return rights

    @__read_transactional
    def get_user_rights(self, user: str, path: str) -> int:
        path, filename = os.path.split(path)
        req = """SELECT subjects.id AS subject_id, rights
        FROM (SELECT users.id FROM users WHERE users.name IS :user
            UNION
            SELECT group_id FROM user_has_group
            WHERE user_id IS (SELECT users.id FROM users WHERE users.name IS :user)) AS subjects
        LEFT JOIN (SELECT shf.subject_id, shf.rights
            FROM files AS f
            JOIN subject_has_file shf
            ON f.id IS shf.file_id AND f.path IS :path AND f.name IS :filename) AS shf
        ON shf.subject_id IS subjects.id"""
        args = {'user': user, 'path': path, 'filename': filename}
        rights = 0xFFFF
        for i in self.__request(req, args):
            if i[1] is None:
                rights = 0
                break
            rights &= i[1]
        return rights
