// Add copy buttons to all code blocks
document.addEventListener('DOMContentLoaded', function() {
    // Add the necessary CSS styles
    const style = document.createElement('style');
    style.textContent = `
        .code-header {
            position: relative;
            background-color: #f6f8fa;
            padding: 8px 16px;
            border: 1px solid #ddd;
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            font-family: monospace;
            display: flex;
            justify-content: flex-end;
            align-items: center;
        }
        
        .copy-button {
            background-color: #f6f8fa;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 4px 8px;
            cursor: pointer;
            font-size: 12px;
            color: #24292e;
        }
        
        .copy-button:hover {
            background-color: #e1e4e8;
        }
        
        div.highlight {
            position: relative;
            border-radius: 0 0 4px 4px;
        }
        
        div.highlight pre {
            margin-top: 0;
            border-top-left-radius: 0;
            border-top-right-radius: 0;
        }
    `;
    document.head.appendChild(style);

    // Find all code blocks
    const codeBlocks = document.querySelectorAll('div.highlight');
    
    // Add copy button to each code block
    codeBlocks.forEach(function(codeBlock, index) {
        // Create the header
        const header = document.createElement('div');
        header.className = 'code-header';
        
        // Create the copy button
        const copyButton = document.createElement('button');
        copyButton.className = 'copy-button';
        copyButton.textContent = 'Copy';
        copyButton.setAttribute('data-index', index);
        
        // Add click event to the copy button
        copyButton.addEventListener('click', function() {
            const code = codeBlock.querySelector('pre').textContent;
            navigator.clipboard.writeText(code).then(function() {
                copyButton.textContent = 'Copied!';
                setTimeout(function() {
                    copyButton.textContent = 'Copy';
                }, 2000);
            }, function() {
                copyButton.textContent = 'Failed to copy';
                setTimeout(function() {
                    copyButton.textContent = 'Copy';
                }, 2000);
            });
        });
        
        // Append the button to the header
        header.appendChild(copyButton);
        
        // Insert the header before the code block
        codeBlock.parentNode.insertBefore(header, codeBlock);
    });
});