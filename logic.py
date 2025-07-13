import sqlite3
from config import DATABASE

skills = [ (_,) for _ in (['Python',  'SQL', 'API', 'Telegram', 'FLASK', 'AI', 'JavaScript', 'HTML', 'CSS'])]
statuses = [ (_,) for _ in (['На этапе проектирования.', 'В процессе разработки.', 'Разработан. Готов к использованию.', 'Обновлен.', 'Завершен. Не поддерживается.'])]

class DB_Manager:
    def __init__(self, database):
        self.database = database # имя базы данных
        
    def create_tables(self):
        con = sqlite3.connect(self.database)
        with con:
            con.execute('''CREATE TABLE projects(
                        project_id INTEGER PRIMARY KEY,
                        user_id INTEGER,
                        project_name TEXT NOT NULL,
                        project_description TEXT,
                        url TEXT,
                        status_id INTEGER,
                        FOREIGN KEY(status_id) REFERENCES status(status_id))
                        ''')
            
            con.execute('''CREATE TABLE skills(
                        skill_id INTEGER PRIMARY KEY,
                        skill_name TEXT)''')
            
            con.execute('''CREATE TABLE project_skills(
                        project_id INTEGER,
                        skill_id INTEGER,
                        FOREIGN KEY(project_id) REFERENCES projects(project_id),
                        FOREIGN KEY(skill_id) REFERENCES skills(skill_id))''')
            
            con.execute('''CREATE TABLE status(
                        status_id INTEGER PRIMARY KEY,
                        status_name TEXT NOT NULL)''')

            # Проверяем и добавляем столбцы, если их нет
            cursor = con.cursor()
            cursor.execute("PRAGMA table_info(projects)")
            columns = [info[1] for info in cursor.fetchall()]

            if 'img_url' not in columns:
                cursor.execute("ALTER TABLE projects ADD COLUMN img_url TEXT")
                print("Столбец 'img_url' добавлен в таблицу 'projects'.")
            else:
                print("Столбец 'img_url' уже существует в таблице 'projects'.")

            if 'img_blob' not in columns:
                cursor.execute("ALTER TABLE projects ADD COLUMN img_blob BLOB")
                print("Столбец 'img_blob' добавлен в таблицу 'projects'.")
            else:
                print("Столбец 'img_blob' уже существует в таблице 'projects'.")

            con.commit()

    def __executemany(self, sql, data):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.executemany(sql, data)
            conn.commit()
    
    def __select_data(self, sql, data = tuple()):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute(sql, data)
            return cur.fetchall()
        
    def default_insert(self):
       # Define default skills and statuses as lists of tuples
        #skills = [
            #('Python',),
            #('JavaScript',),
            #('HTML',),
            #('CSS',)
            #('Telegram',),
            #('API',),
            #('FLASK',),
            #('AI',),
            #('SQL',),  
        #]
        #statuses = [
            #('In Progress',),
            #('Completed',),
            #('On Hold',)
        #]

        sql = 'INSERT OR IGNORE INTO skills (skill_name) values(?)'
        data = skills
        self.__executemany(sql, data)
        sql = 'INSERT OR IGNORE INTO status (status_name) values(?)'
        data = statuses
        self.__executemany(sql, data)


    def insert_project(self, data):
        sql = """INSERT INTO projects 
                (user_id, project_name, project_description, url, status_id) 
                values(?, ?, ?, ?, ?)"""
        self.__executemany(sql, data)


    def insert_skill(self, user_id, project_name, skill):
        sql = 'SELECT project_id FROM projects WHERE project_name = ? AND user_id = ?'
        project_id = self.__select_data(sql, (project_name, user_id))[0][0]
        skill_id = self.__select_data('SELECT skill_id FROM skills WHERE skill_name = ?', (skill,))[0][0]
        data = [(project_id, skill_id)]
        sql = 'INSERT OR IGNORE INTO project_skills VALUES(?, ?)'
        self.__executemany(sql, data)


    def get_statuses(self):
        sql="SELECT status_name from status"
        return self.__select_data(sql)
        

    def get_status_id(self, status_name):
        sql = 'SELECT status_id FROM status WHERE status_name = ?'
        res = self.__select_data(sql, (status_name,))
        if res: return res[0][0]
        else: return None

    def get_projects(self, user_id):
        sql="""SELECT * FROM projects 
               WHERE user_id = ?"""
        return self.__select_data(sql, data = (user_id,))
        
    def get_project_id(self, project_name, user_id):
        return self.__select_data(sql='SELECT project_id FROM projects WHERE project_name = ? AND user_id = ?  ', data = (project_name, user_id,))[0][0]
        
    def get_skills(self):
        return self.__select_data(sql='SELECT * FROM skills')
    
    def get_project_skills(self, project_name):
        res = self.__select_data(sql='''SELECT skill_name FROM projects 
JOIN project_skills ON projects.project_id = project_skills.project_id 
JOIN skills ON skills.skill_id = project_skills.skill_id 
WHERE project_name = ?''', data = (project_name,) )
        return ', '.join([x[0] for x in res])
    
    def get_project_info(self, user_id, project_name):
        sql = """
SELECT project_name, description, url, status_name FROM projects 
JOIN status ON
status.status_id = projects.status_id
WHERE project_name=? AND user_id=?
"""
        return self.__select_data(sql=sql, data = (project_name, user_id))


    def update_projects(self, param, data):
        sql = f"""UPDATE projects SET {param} = ? 
                  WHERE project_name = ? AND user_id = ?"""
        self.__executemany(sql, [data]) 

    def update_status(self, status_id, new_status_name):
        sql = "UPDATE status SET status_name = ? WHERE status_id = ?"
        self.__executemany(sql, [(new_status_name, status_id)])
        print(f"Статус с id={status_id} обновлён на '{new_status_name}'.")

    def update_skill(self, skill_id, new_skill_name):
        sql = "UPDATE skills SET skill_name = ? WHERE skill_id = ?"
        self.__executemany(sql, [(new_skill_name, skill_id)])
        print(f"Навык с id={skill_id} обновлён на '{new_skill_name}'.")


    def delete_project(self, user_id, project_id):
        sql = """DELETE FROM projects 
                 WHERE user_id = ? AND project_id = ? """
        self.__executemany(sql, [(user_id, project_id)])
    
    def delete_skill(self, project_id, skill_id):
        sql = """DELETE FROM skills 
                WHERE skill_id = ? AND project_id = ?
"""
        self.__executemany(sql, [(skill_id, project_id)])

    def delete_status_by_id(self, status_id):
        sql = "DELETE FROM status WHERE status_id = ?"
        self.__executemany(sql, [(status_id,)])
        print(f"Статус с id={status_id} удалён.")

    def add_skill(self, skill_name):
        sql = "INSERT INTO skills (skill_name) VALUES (?)"
        self.__executemany(sql, [(skill_name,)])
        print(f"Навык '{skill_name}' добавлен.")

    def add_column_if_not_exists(db_path, table_name, column_name, column_type):
        """
        Добавляет столбец в таблицу, если он не существует.
        
        :param db_path: Путь к базе данных SQLite.
        :param table_name: Имя таблицы, в которую нужно добавить столбец.
        :param column_name: Имя столбца, который нужно добавить.
        :param column_type: Тип данных столбца (например, 'TEXT', 'INTEGER').
        """
        if not db_path or not table_name or not column_name or not column_type:
            raise ValueError("Все параметры должны быть указаны.")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [info[1] for info in cursor.fetchall()]

        if column_name not in columns:
            alter_query = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
            cursor.execute(alter_query)
            print(f"Столбец '{column_name}' добавлен в таблицу '{table_name}'.")
        else:
            print(f"Столбец '{column_name}' уже существует в таблице '{table_name}'.")

    def insert_full_project(self, user_id, name, description, url, status_id, img_url, img_blob):
        sql = """
            INSERT INTO projects (
                user_id, project_name, project_description, url, status_id, img_url, img_blob
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        self.__executemany(sql, [(user_id, name, description, url, status_id, img_url, img_blob)])


         


if __name__ == '__main__':
    manager = DB_Manager(DATABASE)
    manager.create_tables()
    manager.default_insert()
    #manager.insert_project([('user_id', 'project_name', 'url', 'status_id')])
    status_id = manager.get_status_id("Разработан. Готов к использованию.")
    manager.insert_project([
        (1, "Телеграм-бот-админ", "Бот для управления чатом." ,"https://github.com/Arsendor/M1L3.git", status_id),
        (1, 'Телеграм-бот-игра /"Покемоны"/', "Игра, где можно получить своего покемона, кормить его, сражаться с ним и не только." ,"https://github.com/Arsendor/M2L2.git", status_id),
        (1, "Телеграм-бот-переводчик", "Бот, предлагающий либо перевод отправленного пользователем сообщения, либо ответ на него." ,"https://github.com/Arsendor/M2L4.git", status_id)
    ])