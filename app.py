from flask import Flask, render_template, request
from bot import get_chatbot_response, save_chat_history_to_s3,chat_history

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def chat_prompt():
    result = None
    if request.method == 'POST':
        prompt = request.form['prompt']
        result = get_chatbot_response(prompt)
        chat_history.append((prompt, result))
    return render_template('index.html', result=result)

@app.route('/exit', methods=['POST'])
def exit_app():
    save_chat_history_to_s3()
    r=print("successfull")# Save chat history before exiting
    return render_template('success.html')

if __name__ == '__main__':
    app.run(debug=True)
