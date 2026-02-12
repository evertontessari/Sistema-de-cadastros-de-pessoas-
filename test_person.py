"""
Unit tests for Person class.
"""
import pytest
from datetime import datetime
from person import Person


class TestPersonValidation:
    """Test person validation."""
    
    def test_valid_person(self):
        """Test creating a valid person."""
        person = Person(
            name="João Silva",
            cpf="12345678909",
            email="joao@example.com",
            birth_date="1990-01-01"
        )
        assert person.name == "João Silva"
        assert person.cpf == "12345678909"
        assert person.email == "joao@example.com"
        assert person.birth_date == "1990-01-01"
    
    def test_invalid_name_empty(self):
        """Test empty name validation."""
        with pytest.raises(ValueError, match="Nome não pode estar vazio"):
            Person(
                name="",
                cpf="12345678909",
                email="joao@example.com",
                birth_date="1990-01-01"
            )
    
    def test_invalid_name_too_short(self):
        """Test name too short."""
        with pytest.raises(ValueError, match="Nome deve ter pelo menos 3 caracteres"):
            Person(
                name="Jo",
                cpf="12345678909",
                email="joao@example.com",
                birth_date="1990-01-01"
            )
    
    def test_invalid_cpf_length(self):
        """Test CPF with invalid length."""
        with pytest.raises(ValueError, match="CPF deve ter 11 dígitos"):
            Person(
                name="João Silva",
                cpf="123456789",
                email="joao@example.com",
                birth_date="1990-01-01"
            )
    
    def test_invalid_cpf_all_same_digits(self):
        """Test CPF with all same digits."""
        with pytest.raises(ValueError, match="CPF inválido"):
            Person(
                name="João Silva",
                cpf="11111111111",
                email="joao@example.com",
                birth_date="1990-01-01"
            )
    
    def test_invalid_cpf_check_digit(self):
        """Test CPF with invalid check digit."""
        with pytest.raises(ValueError, match="CPF inválido"):
            Person(
                name="João Silva",
                cpf="12345678900",
                email="joao@example.com",
                birth_date="1990-01-01"
            )
    
    def test_valid_cpf_with_formatting(self):
        """Test CPF with formatting characters."""
        person = Person(
            name="João Silva",
            cpf="123.456.789-09",
            email="joao@example.com",
            birth_date="1990-01-01"
        )
        assert person.cpf == "12345678909"
    
    def test_invalid_email_empty(self):
        """Test empty email."""
        with pytest.raises(ValueError, match="Email não pode estar vazio"):
            Person(
                name="João Silva",
                cpf="12345678909",
                email="",
                birth_date="1990-01-01"
            )
    
    def test_invalid_email_format(self):
        """Test invalid email format."""
        with pytest.raises(ValueError, match="Email inválido"):
            Person(
                name="João Silva",
                cpf="12345678909",
                email="invalid-email",
                birth_date="1990-01-01"
            )
    
    def test_email_lowercase_conversion(self):
        """Test email is converted to lowercase."""
        person = Person(
            name="João Silva",
            cpf="12345678909",
            email="JOAO@EXAMPLE.COM",
            birth_date="1990-01-01"
        )
        assert person.email == "joao@example.com"
    
    def test_invalid_birth_date_format(self):
        """Test invalid birth date format."""
        with pytest.raises(ValueError, match="Data de nascimento deve estar no formato YYYY-MM-DD"):
            Person(
                name="João Silva",
                cpf="12345678909",
                email="joao@example.com",
                birth_date="01/01/1990"
            )
    
    def test_invalid_birth_date_future(self):
        """Test birth date in the future."""
        future_date = (datetime.now().year + 1)
        with pytest.raises(ValueError, match="Data de nascimento não pode ser no futuro"):
            Person(
                name="João Silva",
                cpf="12345678909",
                email="joao@example.com",
                birth_date=f"{future_date}-01-01"
            )
    
    def test_invalid_birth_date_too_old(self):
        """Test birth date too old."""
        with pytest.raises(ValueError, match="Data de nascimento inválida"):
            Person(
                name="João Silva",
                cpf="12345678909",
                email="joao@example.com",
                birth_date="1800-01-01"
            )
    
    def test_optional_fields(self):
        """Test person with optional fields."""
        person = Person(
            name="João Silva",
            cpf="12345678909",
            email="joao@example.com",
            birth_date="1990-01-01",
            phone="11999999999",
            address="Rua das Flores, 123"
        )
        assert person.phone == "11999999999"
        assert person.address == "Rua das Flores, 123"
    
    def test_to_dict(self):
        """Test converting person to dictionary."""
        person = Person(
            name="João Silva",
            cpf="12345678909",
            email="joao@example.com",
            birth_date="1990-01-01"
        )
        person_dict = person.to_dict()
        
        assert person_dict['name'] == "João Silva"
        assert person_dict['cpf'] == "12345678909"
        assert person_dict['email'] == "joao@example.com"
        assert person_dict['birth_date'] == "1990-01-01"
    
    def test_str_representation(self):
        """Test string representation."""
        person = Person(
            name="João Silva",
            cpf="12345678909",
            email="joao@example.com",
            birth_date="1990-01-01"
        )
        assert str(person) == "João Silva (CPF: 12345678909)"
