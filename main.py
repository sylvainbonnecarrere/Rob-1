import logging
from gui import creer_interface

# Configure logging
logging.basicConfig(
    filename="application.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def main():
    """Point d'entrée principal de l'application."""
    logging.info("Application démarrée.")
    try:
        creer_interface()
    except Exception as e:
        logging.error(f"Erreur lors de l'exécution de l'interface : {e}")
        raise

if __name__ == "__main__":
    main()