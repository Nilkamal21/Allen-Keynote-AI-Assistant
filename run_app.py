import uvicorn

if __name__ == "__main__":
    print("\n========================================================")
    print("  Starting Allen's Keynotes AI Assistant Web Application")
    print("  Open your browser at: http://127.0.0.1:8000")
    print("========================================================\n")
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
