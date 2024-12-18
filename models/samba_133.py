from smbprotocol.connection import Connection
from smbprotocol.session import Session
from smbprotocol.tree import TreeConnect
from smbprotocol.open import Open
from models.log import Log
def upload_to_M(excel_file_path):
    server = "10.80.160.133"
    share = "dades"
    username = "GTGIR\\43637832R"
    password = "Uri_00000023"
    remote_file_path = "\\laboratori\\LabDiagnosticMolecular\\Compendium\\LDG_REG08_Compendium\\LDG_REG08_001_Compendium_MANE_CLINICAL\\"
    

    # Establish a connection
    connection = Connection(uuid="unique_connection", server=server, port=445)
    connection.connect()
    
    try:
        # Authenticate with the session
        session = Session(connection, username=username, password=password)
        session.connect()
        
        # Connect to the shared folder
        tree = TreeConnect(session, f"\\\\{server}\\{share}")
        tree.connect()
        # Example: List files or open a specific file
        Log.info(f"Connected to //{server}/{share}")
        # Open the remote file for writing (create if not exists)
        with Open(tree, remote_file_path, "wb") as remote_file:
            # Read the local Excel file
            with open(excel_file_path, "rb") as local_file:
                file_content = local_file.read()
        
            # Write the content to the remote file
            remote_file.write(file_content)
            Log.info(f"Successfully uploaded {local_file_path} to {remote_file_path}")


    finally:
        # Cleanup
        connection.disconnect()
