#!/usr/bin/env python3
"""
Sistema de Cadastro de Pessoas - CLI
Command-line interface for person registration system.
"""
import sys
from typing import Optional
from database import DatabaseManager
from person import Person


class CLI:
    """Command-line interface for person registration system."""
    
    def __init__(self):
        """Initialize CLI."""
        self.db = DatabaseManager()
    
    def run(self):
        """Run the CLI application."""
        print("=" * 60)
        print("Sistema de Cadastro de Pessoas".center(60))
        print("=" * 60)
        
        while True:
            self.show_menu()
            choice = input("\nEscolha uma opção: ").strip()
            
            if choice == '1':
                self.add_person()
            elif choice == '2':
                self.list_people()
            elif choice == '3':
                self.search_person()
            elif choice == '4':
                self.update_person()
            elif choice == '5':
                self.delete_person()
            elif choice == '6':
                self.show_statistics()
            elif choice == '0':
                print("\nSaindo do sistema. Até logo!")
                break
            else:
                print("\nOpção inválida! Tente novamente.")
            
            input("\nPressione Enter para continuar...")
    
    @staticmethod
    def show_menu():
        """Display main menu."""
        print("\n" + "=" * 60)
        print("MENU PRINCIPAL".center(60))
        print("=" * 60)
        print("1. Adicionar nova pessoa")
        print("2. Listar todas as pessoas")
        print("3. Buscar pessoa")
        print("4. Atualizar cadastro")
        print("5. Remover pessoa")
        print("6. Estatísticas")
        print("0. Sair")
        print("=" * 60)
    
    def add_person(self):
        """Add a new person to the system."""
        print("\n" + "-" * 60)
        print("ADICIONAR NOVA PESSOA".center(60))
        print("-" * 60)
        
        try:
            name = input("Nome completo: ").strip()
            cpf = input("CPF (apenas números): ").strip()
            email = input("Email: ").strip()
            birth_date = input("Data de nascimento (YYYY-MM-DD): ").strip()
            phone = input("Telefone (opcional): ").strip() or None
            address = input("Endereço (opcional): ").strip() or None
            
            person = Person(
                name=name,
                cpf=cpf,
                email=email,
                birth_date=birth_date,
                phone=phone,
                address=address
            )
            
            person_id = self.db.add_person(person)
            print(f"\n✓ Pessoa cadastrada com sucesso! ID: {person_id}")
            
        except ValueError as e:
            print(f"\n✗ Erro de validação: {e}")
        except Exception as e:
            print(f"\n✗ Erro ao cadastrar pessoa: {e}")
    
    def list_people(self):
        """List all registered people."""
        print("\n" + "-" * 60)
        print("LISTA DE PESSOAS CADASTRADAS".center(60))
        print("-" * 60)
        
        people = self.db.get_all_people()
        
        if not people:
            print("\nNenhuma pessoa cadastrada.")
            return
        
        for person in people:
            self.display_person(person)
    
    def search_person(self):
        """Search for a person."""
        print("\n" + "-" * 60)
        print("BUSCAR PESSOA".center(60))
        print("-" * 60)
        
        query = input("Digite nome, CPF ou email para buscar: ").strip()
        
        if not query:
            print("\nBusca cancelada.")
            return
        
        people = self.db.search_people(query)
        
        if not people:
            print("\nNenhuma pessoa encontrada.")
            return
        
        print(f"\n{len(people)} pessoa(s) encontrada(s):")
        for person in people:
            self.display_person(person)
    
    def update_person(self):
        """Update person information."""
        print("\n" + "-" * 60)
        print("ATUALIZAR CADASTRO".center(60))
        print("-" * 60)
        
        try:
            person_id = int(input("ID da pessoa: ").strip())
            person = self.db.get_person_by_id(person_id)
            
            if not person:
                print(f"\nPessoa com ID {person_id} não encontrada.")
                return
            
            print("\nDados atuais:")
            self.display_person(person)
            
            print("\nDeixe em branco para manter o valor atual.")
            
            name = input(f"Nome [{person.name}]: ").strip() or person.name
            email = input(f"Email [{person.email}]: ").strip() or person.email
            birth_date = input(f"Data de nascimento [{person.birth_date}]: ").strip() or person.birth_date
            phone = input(f"Telefone [{person.phone or 'N/A'}]: ").strip()
            phone = phone if phone else person.phone
            address = input(f"Endereço [{person.address or 'N/A'}]: ").strip()
            address = address if address else person.address
            
            # Create updated person object
            updated_person = Person(
                person_id=person.id,
                name=name,
                cpf=person.cpf,  # CPF cannot be changed
                email=email,
                birth_date=birth_date,
                phone=phone,
                address=address
            )
            
            if self.db.update_person(updated_person):
                print("\n✓ Cadastro atualizado com sucesso!")
            else:
                print("\n✗ Erro ao atualizar cadastro.")
                
        except ValueError:
            print("\n✗ ID inválido.")
        except Exception as e:
            print(f"\n✗ Erro ao atualizar pessoa: {e}")
    
    def delete_person(self):
        """Delete a person from the system."""
        print("\n" + "-" * 60)
        print("REMOVER PESSOA".center(60))
        print("-" * 60)
        
        try:
            person_id = int(input("ID da pessoa: ").strip())
            person = self.db.get_person_by_id(person_id)
            
            if not person:
                print(f"\nPessoa com ID {person_id} não encontrada.")
                return
            
            print("\nDados da pessoa a ser removida:")
            self.display_person(person)
            
            confirm = input("\nConfirma a remoção? (S/N): ").strip().upper()
            
            if confirm == 'S':
                if self.db.delete_person(person_id):
                    print("\n✓ Pessoa removida com sucesso!")
                else:
                    print("\n✗ Erro ao remover pessoa.")
            else:
                print("\nRemoção cancelada.")
                
        except ValueError:
            print("\n✗ ID inválido.")
        except Exception as e:
            print(f"\n✗ Erro ao remover pessoa: {e}")
    
    def show_statistics(self):
        """Display system statistics."""
        print("\n" + "-" * 60)
        print("ESTATÍSTICAS DO SISTEMA".center(60))
        print("-" * 60)
        
        stats = self.db.get_statistics()
        
        print(f"\nTotal de pessoas cadastradas: {stats['total_pessoas']}")
        print(f"Último cadastro: {stats['ultimo_cadastro'] or 'N/A'}")
    
    @staticmethod
    def display_person(person: Person):
        """Display person information."""
        print("\n" + "─" * 60)
        print(f"ID: {person.id}")
        print(f"Nome: {person.name}")
        print(f"CPF: {person.cpf}")
        print(f"Email: {person.email}")
        print(f"Data de Nascimento: {person.birth_date}")
        print(f"Telefone: {person.phone or 'N/A'}")
        print(f"Endereço: {person.address or 'N/A'}")
        print("─" * 60)


def main():
    """Main entry point."""
    try:
        cli = CLI()
        cli.run()
    except KeyboardInterrupt:
        print("\n\nPrograma interrompido pelo usuário.")
        sys.exit(0)
    except Exception as e:
        print(f"\nErro inesperado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
