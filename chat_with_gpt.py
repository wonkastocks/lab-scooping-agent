import os
import sys
from dotenv import load_dotenv
from openai import OpenAI

def print_help():
    print("\nCommands:")
    print("  /help    - Show this help message")
    print("  /clear   - Clear the conversation history")
    print("  /exit    - Exit the program")
    print("  /model   - Show current model")
    print("  /files   - List available files")
    print("  /use <id> - Use a specific file for context")
    print("  /clear_files - Clear all files from context")

def main():
    # Load environment variables
    load_dotenv()
    
    # Get API key from environment variables
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found in .env file")
        return

    try:
        # Initialize the OpenAI client
        client = OpenAI(api_key=api_key)
        
        # Default model and messages list
        model = "gpt-4-turbo"
        messages = [
            {"role": "system", "content": "You are a helpful assistant. You have access to various Bible translations and religious texts."}
        ]
        
        # Files to use as context
        file_ids = []
        
        print("Chat with ChatGPT (type /help for commands, /exit to quit)")
        print("-" * 60)
        
        while True:
            try:
                # Get user input
                user_input = input("\nYou: ").strip()
                
                # Handle commands
                if user_input.startswith('/'):
                    cmd = user_input[1:].lower().split()
                    
                    if not cmd:
                        continue
                        
                    if cmd[0] == 'exit':
                        print("Goodbye!")
                        break
                        
                    elif cmd[0] == 'help':
                        print_help()
                        
                    elif cmd[0] == 'clear':
                        messages = [m for m in messages if m["role"] == "system"]
                        print("Conversation history cleared.")
                        
                    elif cmd[0] == 'model':
                        print(f"Current model: {model}")
                        
                    elif cmd[0] == 'files':
                        if file_ids:
                            files = client.files.list()
                            print("\nFiles in context:")
                            for fid in file_ids:
                                for f in files.data:
                                    if f.id == fid:
                                        print(f"- {f.filename} (ID: {f.id})")
                        else:
                            print("No files in context. Use /use <file_id> to add files.")
                            
                    elif cmd[0] == 'use' and len(cmd) > 1:
                        file_id = cmd[1]
                        try:
                            # Verify the file exists
                            file_info = client.files.retrieve(file_id)
                            if file_id not in file_ids:
                                file_ids.append(file_id)
                                print(f"Added file: {file_info.filename} (ID: {file_id})")
                            else:
                                print(f"File already in context: {file_info.filename}")
                        except Exception as e:
                            print(f"Error: {str(e)}")
                            
                    elif cmd[0] == 'clear_files':
                        file_ids = []
                        print("Cleared all files from context.")
                        
                    else:
                        print("Unknown command. Type /help for available commands.")
                    continue
                
                # Add user message to conversation
                messages.append({"role": "user", "content": user_input})
                
                # Show typing indicator
                print("\nAssistant: ", end='', flush=True)
                
                # Prepare the request with files if any
                request_data = {
                    "model": model,
                    "messages": messages,
                }
                
                if file_ids:
                    request_data["tools"] = [{"type": "file_search"}]
                    request_data["file_ids"] = file_ids
                
                # Stream the response
                full_response = ""
                for chunk in client.chat.completions.create(
                    **request_data,
                    stream=True
                ):
                    if chunk.choices and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        print(content, end='', flush=True)
                        full_response += content
                
                # Add assistant's response to messages
                if full_response:
                    messages.append({"role": "assistant", "content": full_response})
                
            except KeyboardInterrupt:
                print("\nType /exit to quit or /help for commands.")
                
            except Exception as e:
                print(f"\nError: {str(e)}")
                
    except Exception as e:
        print(f"Failed to initialize OpenAI client: {str(e)}")

if __name__ == "__main__":
    main()
