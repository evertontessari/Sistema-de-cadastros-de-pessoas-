"""
Unit tests for DatabaseManager class.
"""
import pytest
import os
from database import DatabaseManager
from person import Person


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    db_path = "test_pessoas.db"
    db = DatabaseManager(db_path)
    yield db
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)


class TestDatabaseManager:
    """Test database operations."""
    
    def test_add_person(self, temp_db):
        """Test adding a person."""
        person = Person(
            name="João Silva",
            cpf="12345678909",
            email="joao@example.com",
            birth_date="1990-01-01"
        )
        person_id = temp_db.add_person(person)
        assert person_id > 0
    
    def test_add_duplicate_cpf(self, temp_db):
        """Test adding person with duplicate CPF."""
        person1 = Person(
            name="João Silva",
            cpf="12345678909",
            email="joao@example.com",
            birth_date="1990-01-01"
        )
        temp_db.add_person(person1)
        
        person2 = Person(
            name="Maria Silva",
            cpf="12345678909",
            email="maria@example.com",
            birth_date="1992-01-01"
        )
        
        with pytest.raises(ValueError, match="CPF já cadastrado no sistema"):
            temp_db.add_person(person2)
    
    def test_get_person_by_id(self, temp_db):
        """Test retrieving person by ID."""
        person = Person(
            name="João Silva",
            cpf="12345678909",
            email="joao@example.com",
            birth_date="1990-01-01"
        )
        person_id = temp_db.add_person(person)
        
        retrieved = temp_db.get_person_by_id(person_id)
        assert retrieved is not None
        assert retrieved.name == "João Silva"
        assert retrieved.cpf == "12345678909"
    
    def test_get_person_by_id_not_found(self, temp_db):
        """Test retrieving non-existent person."""
        retrieved = temp_db.get_person_by_id(999)
        assert retrieved is None
    
    def test_get_person_by_cpf(self, temp_db):
        """Test retrieving person by CPF."""
        person = Person(
            name="João Silva",
            cpf="12345678909",
            email="joao@example.com",
            birth_date="1990-01-01"
        )
        temp_db.add_person(person)
        
        retrieved = temp_db.get_person_by_cpf("12345678909")
        assert retrieved is not None
        assert retrieved.name == "João Silva"
    
    def test_get_all_people(self, temp_db):
        """Test retrieving all people."""
        person1 = Person(
            name="João Silva",
            cpf="12345678909",
            email="joao@example.com",
            birth_date="1990-01-01"
        )
        person2 = Person(
            name="Maria Silva",
            cpf="98765432100",
            email="maria@example.com",
            birth_date="1992-01-01"
        )
        
        temp_db.add_person(person1)
        temp_db.add_person(person2)
        
        people = temp_db.get_all_people()
        assert len(people) == 2
    
    def test_search_people_by_name(self, temp_db):
        """Test searching people by name."""
        person1 = Person(
            name="João Silva",
            cpf="12345678909",
            email="joao@example.com",
            birth_date="1990-01-01"
        )
        person2 = Person(
            name="Maria Santos",
            cpf="98765432100",
            email="maria@example.com",
            birth_date="1992-01-01"
        )
        
        temp_db.add_person(person1)
        temp_db.add_person(person2)
        
        results = temp_db.search_people("Silva")
        assert len(results) == 1
        assert results[0].name == "João Silva"
    
    def test_search_people_by_cpf(self, temp_db):
        """Test searching people by CPF."""
        person = Person(
            name="João Silva",
            cpf="12345678909",
            email="joao@example.com",
            birth_date="1990-01-01"
        )
        temp_db.add_person(person)
        
        results = temp_db.search_people("123456")
        assert len(results) == 1
        assert results[0].cpf == "12345678909"
    
    def test_update_person(self, temp_db):
        """Test updating person information."""
        person = Person(
            name="João Silva",
            cpf="12345678909",
            email="joao@example.com",
            birth_date="1990-01-01"
        )
        person_id = temp_db.add_person(person)
        
        # Update person
        updated_person = Person(
            person_id=person_id,
            name="João Silva Santos",
            cpf="12345678909",
            email="joao.santos@example.com",
            birth_date="1990-01-01",
            phone="11999999999"
        )
        
        success = temp_db.update_person(updated_person)
        assert success is True
        
        # Verify update
        retrieved = temp_db.get_person_by_id(person_id)
        assert retrieved.name == "João Silva Santos"
        assert retrieved.email == "joao.santos@example.com"
        assert retrieved.phone == "11999999999"
    
    def test_update_person_not_found(self, temp_db):
        """Test updating non-existent person."""
        person = Person(
            person_id=999,
            name="João Silva",
            cpf="12345678909",
            email="joao@example.com",
            birth_date="1990-01-01"
        )
        
        success = temp_db.update_person(person)
        assert success is False
    
    def test_delete_person(self, temp_db):
        """Test deleting a person."""
        person = Person(
            name="João Silva",
            cpf="12345678909",
            email="joao@example.com",
            birth_date="1990-01-01"
        )
        person_id = temp_db.add_person(person)
        
        success = temp_db.delete_person(person_id)
        assert success is True
        
        # Verify deletion
        retrieved = temp_db.get_person_by_id(person_id)
        assert retrieved is None
    
    def test_delete_person_not_found(self, temp_db):
        """Test deleting non-existent person."""
        success = temp_db.delete_person(999)
        assert success is False
    
    def test_get_statistics(self, temp_db):
        """Test getting database statistics."""
        person1 = Person(
            name="João Silva",
            cpf="12345678909",
            email="joao@example.com",
            birth_date="1990-01-01"
        )
        person2 = Person(
            name="Maria Silva",
            cpf="98765432100",
            email="maria@example.com",
            birth_date="1992-01-01"
        )
        
        temp_db.add_person(person1)
        temp_db.add_person(person2)
        
        stats = temp_db.get_statistics()
        assert stats['total_pessoas'] == 2
        assert stats['ultimo_cadastro'] is not None
