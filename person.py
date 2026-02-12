"""
Person model with validation and data management.
"""
import re
from datetime import datetime
from typing import Optional


class Person:
    """Represents a person in the registration system."""
    
    def __init__(
        self,
        name: str,
        cpf: str,
        email: str,
        birth_date: str,
        phone: Optional[str] = None,
        address: Optional[str] = None,
        person_id: Optional[int] = None
    ):
        """
        Initialize a Person object.
        
        Args:
            name: Full name of the person
            cpf: Brazilian CPF (11 digits)
            email: Email address
            birth_date: Date of birth (YYYY-MM-DD format)
            phone: Optional phone number
            address: Optional address
            person_id: Optional database ID
        """
        self.id = person_id
        self.name = self._validate_name(name)
        self.cpf = self._validate_cpf(cpf)
        self.email = self._validate_email(email)
        self.birth_date = self._validate_birth_date(birth_date)
        self.phone = phone
        self.address = address
        self.created_at = datetime.now().isoformat()
    
    @staticmethod
    def _validate_name(name: str) -> str:
        """Validate person name."""
        if not name or not name.strip():
            raise ValueError("Nome não pode estar vazio")
        if len(name.strip()) < 3:
            raise ValueError("Nome deve ter pelo menos 3 caracteres")
        return name.strip()
    
    @staticmethod
    def _validate_cpf(cpf: str) -> str:
        """Validate Brazilian CPF."""
        # Remove non-numeric characters
        cpf_clean = re.sub(r'\D', '', cpf)
        
        if len(cpf_clean) != 11:
            raise ValueError("CPF deve ter 11 dígitos")
        
        # Check if all digits are the same
        if cpf_clean == cpf_clean[0] * 11:
            raise ValueError("CPF inválido")
        
        # Validate CPF check digits
        def calculate_digit(cpf_partial: str, weight: int) -> int:
            total = sum(int(cpf_partial[i]) * (weight - i) for i in range(len(cpf_partial)))
            remainder = total % 11
            return 0 if remainder < 2 else 11 - remainder
        
        first_digit = calculate_digit(cpf_clean[:9], 10)
        second_digit = calculate_digit(cpf_clean[:10], 11)
        
        if int(cpf_clean[9]) != first_digit or int(cpf_clean[10]) != second_digit:
            raise ValueError("CPF inválido")
        
        return cpf_clean
    
    @staticmethod
    def _validate_email(email: str) -> str:
        """Validate email address."""
        if not email or not email.strip():
            raise ValueError("Email não pode estar vazio")
        
        # Simple email validation regex
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email.strip()):
            raise ValueError("Email inválido")
        
        return email.strip().lower()
    
    @staticmethod
    def _validate_birth_date(birth_date: str) -> str:
        """Validate birth date."""
        try:
            date_obj = datetime.strptime(birth_date, '%Y-%m-%d')
            
            # Check if date is not in the future
            if date_obj > datetime.now():
                raise ValueError("Data de nascimento não pode ser no futuro")
            
            # Check if person is not too old (reasonable limit: 150 years)
            age = (datetime.now() - date_obj).days / 365.25
            if age > 150:
                raise ValueError("Data de nascimento inválida")
            
            return birth_date
        except ValueError as e:
            if "does not match format" in str(e):
                raise ValueError("Data de nascimento deve estar no formato YYYY-MM-DD")
            raise
    
    def to_dict(self) -> dict:
        """Convert person to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'cpf': self.cpf,
            'email': self.email,
            'birth_date': self.birth_date,
            'phone': self.phone,
            'address': self.address,
            'created_at': self.created_at
        }
    
    def __repr__(self) -> str:
        return f"Person(id={self.id}, name='{self.name}', cpf='{self.cpf}')"
    
    def __str__(self) -> str:
        return f"{self.name} (CPF: {self.cpf})"
