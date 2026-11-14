"""Execute the notebook using the prepared project kernel; fail on any cell error."""
from pathlib import Path
import nbformat
from nbclient import NotebookClient

root=Path(__file__).resolve().parent
notebook=nbformat.read(root/"notebook.ipynb",as_version=4)
client=NotebookClient(notebook,timeout=900,kernel_name="jaya-reference",resources={"metadata":{"path":str(root)}})
client.execute()
nbformat.write(notebook,root/"notebook.ipynb")
print("Executed all",sum(c.cell_type=="code" for c in notebook.cells),"code cells without errors")
