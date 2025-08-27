import subprocess
import sys
import os

def generate_grpc_files():
    """Generate Python files from proto file"""
    proto_file = "file.proto"
    output_dir = "cli"
    
    if not os.path.exists(proto_file):
        print(f"Error: {proto_file} not found")
        sys.exit(1)
    
    try:
        # Generate Python files
        cmd = [
            sys.executable, "-m", "grpc_tools.protoc",
            f"--python_out={output_dir}",
            f"--grpc_python_out={output_dir}",
            "--proto_path=.",
            proto_file
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error generating proto files: {result.stderr}")
            sys.exit(1)
        
        print("Generated proto files successfully:")
        print(f"  {output_dir}/file_pb2.py")
        print(f"  {output_dir}/file_pb2_grpc.py")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    generate_grpc_files()