/**
 * Collaboration JavaScript
 * 
 * Handles real-time collaboration features including comments, notifications,
 * and live updates for the AI Executive Suite.
 */

class CollaborationManager {
    constructor(decisionId) {
        this.decisionId = decisionId;
        this.socket = null;
        this.notificationPermission = 'default';
        this.lastActivityTime = Date.now();
        this.refreshInterval = null;
        this.mentionUsers = [];
        
        this.init();
    }
    
    init() {
        this.requestNotificationPermission();
        this.setupEventListeners();
        this.startPeriodicRefresh();
        this.loadMentionUsers();
    }
    
    requestNotificationPermission() {
        if ('Notification' in window) {
            Notification.requestPermission().then(permission => {
                this.notificationPermission = permission;
            });
        }
    }
    
    setupEventListeners() {
        // Comment form submission
        const commentForm = document.getElementById('comment-form');
        if (commentForm) {
            commentForm.addEventListener('submit', (e) => this.handleCommentSubmit(e));
        }
        
        // Reply buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('reply-btn')) {
                this.showReplyForm(e.target.dataset.commentId);
            }
            
            if (e.target.classList.contains('edit-btn')) {
                this.showEditForm(e.target.dataset.commentId);
            }
            
            if (e.target.classList.contains('delete-btn')) {
                this.deleteComment(e.target.dataset.commentId);
            }
            
            if (e.target.classList.contains('mention-user')) {
                this.insertMention(e.target.dataset.userId, e.target.dataset.username);
            }
        });
        
        // Mention detection in textarea
        const commentTextarea = document.getElementById('comment-content');
        if (commentTextarea) {
            commentTextarea.addEventListener('input', (e) => this.handleMentionInput(e));
            commentTextarea.addEventListener('keydown', (e) => this.handleMentionKeydown(e));
        }
        
        // Activity tracking
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.refreshData();
            }
        });
    }
    
    startPeriodicRefresh() {
        // Refresh every 30 seconds when page is visible
        this.refreshInterval = setInterval(() => {
            if (!document.hidden) {
                this.refreshData();
            }
        }, 30000);
    }
    
    async refreshData() {
        try {
            await Promise.all([
                this.loadComments(),
                this.loadActivity(),
                this.checkNotifications()
            ]);
        } catch (error) {
            console.error('Error refreshing data:', error);
        }
    }
    
    async loadComments() {
        try {
            const response = await fetch(`/api/collaboration/comments/${this.decisionId}`);
            if (response.ok) {
                const data = await response.json();
                this.updateCommentsDisplay(data.comments);
                this.updateCommentCount(data.total_count);
            }
        } catch (error) {
            console.error('Error loading comments:', error);
        }
    }
    
    async loadActivity() {
        try {
            const response = await fetch(`/api/collaboration/history/${this.decisionId}`);
            if (response.ok) {
                const data = await response.json();
                this.updateActivityDisplay(data.history);
            }
        } catch (error) {
            console.error('Error loading activity:', error);
        }
    }
    
    async checkNotifications() {
        try {
            const response = await fetch('/api/collaboration/notifications?status=unread&limit=5');
            if (response.ok) {
                const data = await response.json();
                this.handleNewNotifications(data.notifications);
            }
        } catch (error) {
            console.error('Error checking notifications:', error);
        }
    }
    
    async loadMentionUsers() {
        try {
            // Load users who can be mentioned (collaborators, decision owner, etc.)
            const response = await fetch(`/api/collaboration/session/${this.decisionId}`);
            if (response.ok) {
                const data = await response.json();
                if (data.session && data.session.participants) {
                    this.mentionUsers = data.session.participants.map(p => ({
                        id: p.user.id,
                        username: p.user.username,
                        name: p.user.name
                    }));
                }
            }
        } catch (error) {
            console.error('Error loading mention users:', error);
        }
    }
    
    async handleCommentSubmit(event) {
        event.preventDefault();
        
        const form = event.target;
        const content = form.querySelector('#comment-content').value.trim();
        const parentId = form.dataset.parentId || null;
        
        if (!content) {
            this.showError('Please enter a comment');
            return;
        }
        
        // Extract mentions from content
        const mentions = this.extractMentions(content);
        
        try {
            const response = await fetch('/api/collaboration/comment', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    decision_id: parseInt(this.decisionId),
                    content: content,
                    parent_id: parentId ? parseInt(parentId) : null,
                    mentions: mentions
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                form.reset();
                this.hideReplyForm();
                await this.loadComments();
                await this.loadActivity();
                this.showSuccess('Comment posted successfully');
            } else {
                const error = await response.json();
                this.showError('Error posting comment: ' + error.error);
            }
        } catch (error) {
            console.error('Error posting comment:', error);
            this.showError('Error posting comment');
        }
    }
    
    showReplyForm(commentId) {
        // Hide any existing reply forms
        this.hideReplyForm();
        
        const commentElement = document.querySelector(`[data-comment-id="${commentId}"]`);
        if (!commentElement) return;
        
        const replyForm = this.createReplyForm(commentId);
        commentElement.appendChild(replyForm);
        
        // Focus on the textarea
        const textarea = replyForm.querySelector('textarea');
        if (textarea) {
            textarea.focus();
        }
    }
    
    createReplyForm(parentId) {
        const form = document.createElement('form');
        form.className = 'reply-form';
        form.dataset.parentId = parentId;
        form.addEventListener('submit', (e) => this.handleCommentSubmit(e));
        
        form.innerHTML = `
            <div class="form-group">
                <textarea class="form-textarea" placeholder="Write a reply..." required></textarea>
            </div>
            <div class="form-actions">
                <button type="submit" class="btn btn-small">Reply</button>
                <button type="button" class="btn btn-secondary btn-small" onclick="this.closest('.reply-form').remove()">Cancel</button>
            </div>
        `;
        
        return form;
    }
    
    hideReplyForm() {
        const existingForms = document.querySelectorAll('.reply-form');
        existingForms.forEach(form => form.remove());
    }
    
    showEditForm(commentId) {
        const commentElement = document.querySelector(`[data-comment-id="${commentId}"] .comment-content`);
        if (!commentElement) return;
        
        const currentContent = commentElement.textContent;
        const editForm = document.createElement('div');
        editForm.className = 'edit-form';
        editForm.innerHTML = `
            <textarea class="form-textarea">${currentContent}</textarea>
            <div class="form-actions">
                <button type="button" class="btn btn-small save-edit-btn">Save</button>
                <button type="button" class="btn btn-secondary btn-small cancel-edit-btn">Cancel</button>
            </div>
        `;
        
        // Replace content with edit form
        commentElement.style.display = 'none';
        commentElement.parentNode.insertBefore(editForm, commentElement.nextSibling);
        
        // Event listeners for edit form
        editForm.querySelector('.save-edit-btn').addEventListener('click', () => {
            this.saveCommentEdit(commentId, editForm.querySelector('textarea').value);
        });
        
        editForm.querySelector('.cancel-edit-btn').addEventListener('click', () => {
            editForm.remove();
            commentElement.style.display = 'block';
        });
        
        editForm.querySelector('textarea').focus();
    }
    
    async saveCommentEdit(commentId, newContent) {
        try {
            // This would be implemented with an edit endpoint
            console.log('Saving edit for comment', commentId, 'with content:', newContent);
            this.showSuccess('Comment edit feature coming soon!');
        } catch (error) {
            console.error('Error saving comment edit:', error);
            this.showError('Error saving edit');
        }
    }
    
    async deleteComment(commentId) {
        if (!confirm('Are you sure you want to delete this comment?')) {
            return;
        }
        
        try {
            // This would be implemented with a delete endpoint
            console.log('Deleting comment', commentId);
            this.showSuccess('Comment delete feature coming soon!');
        } catch (error) {
            console.error('Error deleting comment:', error);
            this.showError('Error deleting comment');
        }
    }
    
    handleMentionInput(event) {
        const textarea = event.target;
        const cursorPos = textarea.selectionStart;
        const textBeforeCursor = textarea.value.substring(0, cursorPos);
        const lastAtIndex = textBeforeCursor.lastIndexOf('@');
        
        if (lastAtIndex !== -1) {
            const mentionText = textBeforeCursor.substring(lastAtIndex + 1);
            if (mentionText.length > 0 && !mentionText.includes(' ')) {
                this.showMentionSuggestions(mentionText, lastAtIndex, textarea);
            } else {
                this.hideMentionSuggestions();
            }
        } else {
            this.hideMentionSuggestions();
        }
    }
    
    handleMentionKeydown(event) {
        const suggestionsList = document.querySelector('.mention-suggestions');
        if (!suggestionsList) return;
        
        const suggestions = suggestionsList.querySelectorAll('.mention-suggestion');
        let selectedIndex = Array.from(suggestions).findIndex(s => s.classList.contains('selected'));
        
        switch (event.key) {
            case 'ArrowDown':
                event.preventDefault();
                selectedIndex = Math.min(selectedIndex + 1, suggestions.length - 1);
                this.updateMentionSelection(suggestions, selectedIndex);
                break;
            case 'ArrowUp':
                event.preventDefault();
                selectedIndex = Math.max(selectedIndex - 1, 0);
                this.updateMentionSelection(suggestions, selectedIndex);
                break;
            case 'Enter':
            case 'Tab':
                event.preventDefault();
                if (selectedIndex >= 0 && suggestions[selectedIndex]) {
                    const user = this.mentionUsers[selectedIndex];
                    this.insertMention(user.id, user.username, event.target);
                }
                break;
            case 'Escape':
                this.hideMentionSuggestions();
                break;
        }
    }
    
    showMentionSuggestions(query, atIndex, textarea) {
        const filteredUsers = this.mentionUsers.filter(user => 
            user.username.toLowerCase().includes(query.toLowerCase()) ||
            (user.name && user.name.toLowerCase().includes(query.toLowerCase()))
        );
        
        if (filteredUsers.length === 0) {
            this.hideMentionSuggestions();
            return;
        }
        
        let suggestionsList = document.querySelector('.mention-suggestions');
        if (!suggestionsList) {
            suggestionsList = document.createElement('div');
            suggestionsList.className = 'mention-suggestions';
            document.body.appendChild(suggestionsList);
        }
        
        suggestionsList.innerHTML = filteredUsers.map((user, index) => `
            <div class="mention-suggestion ${index === 0 ? 'selected' : ''}" 
                 data-user-id="${user.id}" 
                 data-username="${user.username}">
                <div class="mention-avatar">${(user.name || user.username).charAt(0).toUpperCase()}</div>
                <div class="mention-info">
                    <div class="mention-name">${user.name || user.username}</div>
                    <div class="mention-username">@${user.username}</div>
                </div>
            </div>
        `).join('');
        
        // Position suggestions near the textarea
        const rect = textarea.getBoundingClientRect();
        suggestionsList.style.position = 'absolute';
        suggestionsList.style.left = rect.left + 'px';
        suggestionsList.style.top = (rect.bottom + 5) + 'px';
        suggestionsList.style.zIndex = '1000';
        
        // Add click handlers
        suggestionsList.querySelectorAll('.mention-suggestion').forEach(suggestion => {
            suggestion.addEventListener('click', () => {
                const userId = suggestion.dataset.userId;
                const username = suggestion.dataset.username;
                this.insertMention(userId, username, textarea);
            });
        });
    }
    
    hideMentionSuggestions() {
        const suggestionsList = document.querySelector('.mention-suggestions');
        if (suggestionsList) {
            suggestionsList.remove();
        }
    }
    
    updateMentionSelection(suggestions, selectedIndex) {
        suggestions.forEach((suggestion, index) => {
            suggestion.classList.toggle('selected', index === selectedIndex);
        });
    }
    
    insertMention(userId, username, textarea = null) {
        if (!textarea) {
            textarea = document.getElementById('comment-content');
        }
        
        const cursorPos = textarea.selectionStart;
        const textBeforeCursor = textarea.value.substring(0, cursorPos);
        const textAfterCursor = textarea.value.substring(cursorPos);
        const lastAtIndex = textBeforeCursor.lastIndexOf('@');
        
        if (lastAtIndex !== -1) {
            const beforeMention = textBeforeCursor.substring(0, lastAtIndex);
            const newText = beforeMention + `@${username} ` + textAfterCursor;
            textarea.value = newText;
            
            // Set cursor position after the mention
            const newCursorPos = beforeMention.length + username.length + 2;
            textarea.setSelectionRange(newCursorPos, newCursorPos);
        }
        
        this.hideMentionSuggestions();
        textarea.focus();
    }
    
    extractMentions(content) {
        const mentionRegex = /@(\w+)/g;
        const mentions = [];
        let match;
        
        while ((match = mentionRegex.exec(content)) !== null) {
            const username = match[1];
            const user = this.mentionUsers.find(u => u.username === username);
            if (user) {
                mentions.push(user.id);
            }
        }
        
        return mentions;
    }
    
    updateCommentsDisplay(comments) {
        const container = document.getElementById('comments-list');
        if (!container) return;
        
        if (comments.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <p>No comments yet. Start the discussion!</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = comments.map(comment => this.renderComment(comment)).join('');
    }
    
    renderComment(comment) {
        const replies = comment.replies ? comment.replies.map(reply => this.renderComment(reply)).join('') : '';
        const userCanEdit = comment.user && comment.user.id === this.currentUserId;
        
        return `
            <div class="comment" data-comment-id="${comment.id}">
                <div class="comment-header">
                    <div class="comment-author-info">
                        <div class="comment-avatar">
                            ${(comment.user?.name || comment.user?.username || 'U').charAt(0).toUpperCase()}
                        </div>
                        <div>
                            <span class="comment-author">${comment.user?.name || comment.user?.username || 'Unknown User'}</span>
                            <span class="comment-time">${this.formatTime(comment.created_at)}</span>
                        </div>
                    </div>
                    ${userCanEdit ? `
                        <div class="comment-menu">
                            <button class="comment-menu-btn">⋯</button>
                            <div class="comment-menu-dropdown">
                                <button class="edit-btn" data-comment-id="${comment.id}">Edit</button>
                                <button class="delete-btn" data-comment-id="${comment.id}">Delete</button>
                            </div>
                        </div>
                    ` : ''}
                </div>
                <div class="comment-content">${this.formatCommentContent(comment.content)}</div>
                <div class="comment-actions">
                    <button class="comment-action reply-btn" data-comment-id="${comment.id}">Reply</button>
                    ${comment.is_edited ? '<span class="comment-edited">Edited</span>' : ''}
                </div>
                ${replies ? `<div class="comment-replies">${replies}</div>` : ''}
            </div>
        `;
    }
    
    formatCommentContent(content) {
        // Convert @mentions to clickable links
        return content.replace(/@(\w+)/g, '<span class="mention">@$1</span>');
    }
    
    updateCommentCount(count) {
        const countElement = document.getElementById('comment-count');
        if (countElement) {
            countElement.textContent = `${count} comment${count !== 1 ? 's' : ''}`;
        }
    }
    
    updateActivityDisplay(history) {
        const container = document.getElementById('activity-list');
        if (!container) return;
        
        if (history.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <p>No recent activity</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = history.slice(0, 10).map(event => `
            <div class="activity-item">
                <div class="activity-description">${event.user_name} ${event.description}</div>
                <div class="activity-time">${this.formatTime(event.timestamp)}</div>
            </div>
        `).join('');
    }
    
    handleNewNotifications(notifications) {
        notifications.forEach(notification => {
            if (this.notificationPermission === 'granted') {
                this.showBrowserNotification(notification);
            }
            this.showInAppNotification(notification);
        });
    }
    
    showBrowserNotification(notification) {
        if ('Notification' in window && this.notificationPermission === 'granted') {
            new Notification(notification.title, {
                body: notification.message,
                icon: '/static/images/logo.png',
                tag: `notification-${notification.id}`
            });
        }
    }
    
    showInAppNotification(notification) {
        const notificationElement = document.createElement('div');
        notificationElement.className = 'in-app-notification';
        notificationElement.innerHTML = `
            <div class="notification-content">
                <div class="notification-title">${notification.title}</div>
                <div class="notification-message">${notification.message}</div>
            </div>
            <button class="notification-close">&times;</button>
        `;
        
        document.body.appendChild(notificationElement);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notificationElement.parentNode) {
                notificationElement.remove();
            }
        }, 5000);
        
        // Close button
        notificationElement.querySelector('.notification-close').addEventListener('click', () => {
            notificationElement.remove();
        });
    }
    
    showSuccess(message) {
        this.showMessage(message, 'success');
    }
    
    showError(message) {
        this.showMessage(message, 'error');
    }
    
    showMessage(message, type) {
        const messageElement = document.createElement('div');
        messageElement.className = `message message-${type}`;
        messageElement.textContent = message;
        
        document.body.appendChild(messageElement);
        
        setTimeout(() => {
            if (messageElement.parentNode) {
                messageElement.remove();
            }
        }, 3000);
    }
    
    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);
        
        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        return date.toLocaleDateString();
    }
    
    destroy() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        this.hideMentionSuggestions();
    }
}

// Initialize collaboration manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);
    const decisionId = urlParams.get('decision_id') || window.location.pathname.split('/').pop();
    
    if (decisionId) {
        window.collaborationManager = new CollaborationManager(decisionId);
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (window.collaborationManager) {
        window.collaborationManager.destroy();
    }
});