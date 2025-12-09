<!-- File: hidecode.tpl -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{{ nb.title }}</title>
    <style>
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        /* Ẩn code cells mặc định */
        .input {
            display: none;
        }
        
        /* Nút toggle để hiện/ẩn code */
        .toggle-code {
            background-color: #4CAF50;
            color: white;
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin: 10px 0;
            font-size: 14px;
        }
        
        .toggle-code:hover {
            background-color: #45a049;
        }
        
        /* Style cho output */
        .output {
            margin: 20px 0;
            padding: 15px;
            border-left: 4px solid #3498db;
            background-color: #f8f9fa;
        }
        
        /* Style cho markdown cells */
        .text_cell_render {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
        }
    </style>
    <script>
        function toggleCode() {
            var codeCells = document.querySelectorAll('.input');
            var button = document.querySelector('.toggle-code');
            
            codeCells.forEach(function(cell) {
                if (cell.style.display === 'none' || cell.style.display === '') {
                    cell.style.display = 'block';
                    button.textContent = 'Ẩn Code';
                } else {
                    cell.style.display = 'none';
                    button.textContent = 'Hiện Code';
                }
            });
        }
        
        // Ẩn code khi trang tải xong
        document.addEventListener('DOMContentLoaded', function() {
            var codeCells = document.querySelectorAll('.input');
            codeCells.forEach(function(cell) {
                cell.style.display = 'none';
            });
        });
    </script>
</head>
<body>
    <div class="container">
        <!-- Thêm nút toggle code -->
        <button class="toggle-code" onclick="toggleCode()">Hiện Code</button>
        
        {% for cell in nb.cells %}
            {% if cell.cell_type == 'code' %}
                <div class="input">
                    <pre><code>{{ cell.source }}</code></pre>
                </div>
                <div class="output">
                    {{ cell.outputs | join('\n') }}
                </div>
            {% elif cell.cell_type == 'markdown' %}
                <div class="text_cell_render">
                    {{ cell.source | markdown2html }}
                </div>
            {% endif %}
        {% endfor %}
    </div>
</body>
</html>