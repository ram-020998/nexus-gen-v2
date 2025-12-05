/**
 * Simple SAIL Code Syntax Highlighter
 * Adds basic syntax highlighting to SAIL code blocks
 */

(function() {
    'use strict';
    
    /**
     * Add copy button to code blocks
     */
    function addCopyButtons() {
        const codeBlocks = document.querySelectorAll('.code-diff-body pre, .code-block-body pre');
        
        codeBlocks.forEach(block => {
            // Skip if copy button already exists
            if (block.parentElement.querySelector('.copy-code-btn')) {
                return;
            }
            
            const copyBtn = document.createElement('button');
            copyBtn.className = 'copy-code-btn';
            copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
            copyBtn.title = 'Copy code';
            
            copyBtn.addEventListener('click', function() {
                const code = block.textContent;
                navigator.clipboard.writeText(code).then(() => {
                    copyBtn.innerHTML = '<i class="fas fa-check"></i>';
                    copyBtn.classList.add('copied');
                    setTimeout(() => {
                        copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
                        copyBtn.classList.remove('copied');
                    }, 2000);
                }).catch(err => {
                    console.error('Failed to copy code:', err);
                });
            });
            
            block.parentElement.style.position = 'relative';
            block.parentElement.appendChild(copyBtn);
        });
    }
    
    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', addCopyButtons);
    } else {
        addCopyButtons();
    }
    
    // Export for manual triggering if needed
    window.sailHighlighter = {
        addCopyButtons: addCopyButtons
    };
})();
