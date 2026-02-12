"""
Database manager for person registration system.
"""
import sqlite3
from typing import List, Optional
from person import Person


class DatabaseManager:
    """Manages database operations for person registration."""
    
    def __init__(self, db_path: str = "pessoas.db"):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pessoas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    cpf TEXT UNIQUE NOT NULL,
                    email TEXT NOT NULL,
                    birth_date TEXT NOT NULL,
                    phone TEXT,
                    address TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()
    
    def add_person(self, person: Person) -> int:
        """
        Add a new person to the database.
        
        Args:
            person: Person object to add
            
        Returns:
            ID of the newly added person
            
        Raises:
            ValueError: If CPF already exists
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO pessoas (name, cpf, email, birth_date, phone, address, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    person.name,
                    person.cpf,
                    person.email,
                    person.birth_date,
                    person.phone,
                    person.address,
                    person.created_at
                ))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed: pessoas.cpf" in str(e):
                raise ValueError("CPF já cadastrado no sistema")
            raise
    
    def get_person_by_id(self, person_id: int) -> Optional[Person]:
        """
        Get person by ID.
        
        Args:
            person_id: Person ID
            
        Returns:
            Person object or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pessoas WHERE id = ?", (person_id,))
            row = cursor.fetchone()
            
            if row:
                return self._row_to_person(row)
            return None
    
    def get_person_by_cpf(self, cpf: str) -> Optional[Person]:
        """
        Get person by CPF.
        
        Args:
            cpf: Person CPF
            
        Returns:
            Person object or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pessoas WHERE cpf = ?", (cpf,))
            row = cursor.fetchone()
            
            if row:
                return self._row_to_person(row)
            return None
    
    def get_all_people(self) -> List[Person]:
        """
        Get all people from database.
        
        Returns:
            List of Person objects
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pessoas ORDER BY name")
            rows = cursor.fetchall()
            
            return [self._row_to_person(row) for row in rows]
    
    def search_people(self, query: str) -> List[Person]:
        """
        Search people by name, CPF, or email.
        
        Args:
            query: Search query
            
        Returns:
            List of matching Person objects
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            search_pattern = f"%{query}%"
            cursor.execute("""
                SELECT * FROM pessoas 
                WHERE name LIKE ? OR cpf LIKE ? OR email LIKE ?
                ORDER BY name
            """, (search_pattern, search_pattern, search_pattern))
            rows = cursor.fetchall()
            
            return [self._row_to_person(row) for row in rows]
    
    def update_person(self, person: Person) -> bool:
        """
        Update person information.
        
        Args:
            person: Person object with updated information
            
        Returns:
            True if updated successfully, False if person not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE pessoas 
                SET name = ?, email = ?, birth_date = ?, phone = ?, address = ?
                WHERE id = ?
            """, (
                person.name,
                person.email,
                person.birth_date,
                person.phone,
                person.address,
                person.id
            ))
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_person(self, person_id: int) -> bool:
        """
        Delete person from database.
        
        Args:
            person_id: Person ID
            
        Returns:
            True if deleted successfully, False if person not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM pessoas WHERE id = ?", (person_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_statistics(self) -> dict:
        """
        Get database statistics.
        
        Returns:
            Dictionary with statistics
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total count
            cursor.execute("SELECT COUNT(*) FROM pessoas")
            total = cursor.fetchone()[0]
            
            # Most recent registration
            cursor.execute("SELECT created_at FROM pessoas ORDER BY created_at DESC LIMIT 1")
            recent = cursor.fetchone()
            most_recent = recent[0] if recent else None
            
            return {
                'total_pessoas': total,
                'ultimo_cadastro': most_recent
            }
    
    @staticmethod
    def _row_to_person(row: tuple) -> Person:
        """Convert database row to Person object."""
        return Person(
            person_id=row[0],
            name=row[1],
            cpf=row[2],
            email=row[3],
            birth_date=row[4],
            phone=row[5],
            address=row[6]
        )
