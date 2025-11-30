# Contributing to YTDownloadX

First off, thank you for considering contributing to YTDownloadX! 🎉

It's people like you that make YTDownloadX such a great tool. We welcome contributions from everyone, whether it's a bug report, feature suggestion, documentation improvement, or code contribution.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Style Guidelines](#style-guidelines)
- [Commit Message Guidelines](#commit-message-guidelines)

---

## 📜 Code of Conduct

This project and everyone participating in it is governed by our commitment to providing a welcoming and inspiring community for all. Please be respectful and constructive in your interactions.

### Our Standards

- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

---

## 🤝 How Can I Contribute?

### 🐛 Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce** the issue
- **Expected behavior** vs **actual behavior**
- **Screenshots** if applicable
- **Environment details** (OS, Python version, browser)
- **Error messages** or logs

**Example:**

```markdown
**Bug:** Download fails for playlist URLs

**Steps to Reproduce:**
1. Paste playlist URL: https://www.youtube.com/playlist?list=...
2. Click "Fetch Details"
3. Select videos and click "Download Selected"

**Expected:** Videos should download
**Actual:** Error message appears: "Download failed"

**Environment:**
- OS: Windows 11
- Python: 3.11.5
- Browser: Chrome 120

**Error Log:**
```
[error log here]
```
```

### 💡 Suggesting Features

Feature suggestions are welcome! Please provide:

- **Clear title and description**
- **Use case** - why is this feature needed?
- **Proposed solution** - how should it work?
- **Alternatives considered**
- **Mockups or examples** if applicable

### 📝 Improving Documentation

Documentation improvements are always appreciated:

- Fix typos or clarify existing docs
- Add examples or tutorials
- Improve API documentation
- Translate documentation

### 💻 Code Contributions

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/AmazingFeature`)
3. **Make your changes**
4. **Test thoroughly**
5. **Commit your changes** (see commit guidelines below)
6. **Push to your fork** (`git push origin feature/AmazingFeature`)
7. **Open a Pull Request**

---

## 🛠️ Development Setup

### Prerequisites

- Python 3.11 or higher
- pip package manager
- Git
- FFmpeg (for video processing)

### Setup Steps

```bash
# 1. Fork and clone the repository
git clone https://github.com/TejasRawool186/Youtube_video_downloader.git
cd ytdownloadx

# 2. Create virtual environment
python -m venv .venv

# 3. Activate virtual environment
# Windows
.\.venv\Scripts\Activate.ps1
# Linux/Mac
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Install development dependencies (if any)
pip install pytest black flake8 mypy

# 6. Run the application
python app.py

# 7. Run tests
python test_app.py
```

### Project Structure

```
ytdownloadx/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── test_app.py           # Test suite
├── templates/            # HTML templates
│   ├── index.html       # Main page
│   └── about.html       # About page
├── static/              # Static assets
│   ├── styles.css       # Main stylesheet
│   ├── particles.js     # Particle animation
│   ├── glare-hover.js   # Glare effect
│   └── image/          # Images
├── downloads/           # Downloaded files (gitignored)
└── resources/           # FFmpeg binaries
```

---

## 🔄 Pull Request Process

### Before Submitting

1. **Test your changes** thoroughly
2. **Update documentation** if needed
3. **Follow code style guidelines**
4. **Ensure no breaking changes** (or document them)
5. **Update CHANGELOG.md** if applicable

### PR Checklist

- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests added/updated and passing
- [ ] Dependent changes merged

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How has this been tested?

## Screenshots (if applicable)
Add screenshots here

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests passing
```

---

## 🎨 Style Guidelines

### Python Code Style

We follow PEP 8 with some modifications:

```python
# Good
def download_video(url: str, format: str = "mp4") -> dict:
    """
    Download a video from YouTube.
    
    Args:
        url: YouTube video URL
        format: Output format (mp4 or mp3)
        
    Returns:
        Dictionary with download status
    """
    if not url:
        raise ValueError("URL is required")
    
    # Implementation here
    return {"status": "success"}

# Bad
def download_video(url,format="mp4"):
    if not url:raise ValueError("URL is required")
    return {"status":"success"}
```

### Key Points

- **Indentation:** 4 spaces (no tabs)
- **Line length:** Max 100 characters
- **Imports:** Group by standard library, third-party, local
- **Naming:**
  - Functions/variables: `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPER_SNAKE_CASE`
- **Type hints:** Use where appropriate
- **Docstrings:** Use for all public functions/classes

### JavaScript Code Style

```javascript
// Good
const downloadVideo = async (url, format = 'mp4') => {
    if (!url) {
        throw new Error('URL is required');
    }
    
    const response = await fetch('/api/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, format })
    });
    
    return response.json();
};

// Bad
function downloadVideo(url,format){
if(!url)throw new Error('URL is required')
return fetch('/api/download',{method:'POST',body:JSON.stringify({url,format})}).then(r=>r.json())
}
```

### CSS Code Style

```css
/* Good */
.feature-card {
    background: rgba(16, 9, 40, 0.8);
    border: 1px solid rgba(111, 76, 255, 0.2);
    border-radius: 12px;
    padding: 2rem;
    transition: all 0.3s ease;
}

.feature-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 20px rgba(111, 76, 255, 0.3);
}

/* Bad */
.feature-card{background:rgba(16,9,40,0.8);border:1px solid rgba(111,76,255,0.2);border-radius:12px;padding:2rem;transition:all 0.3s ease;}
.feature-card:hover{transform:translateY(-5px);box-shadow:0 8px 20px rgba(111,76,255,0.3);}
```

---

## 📝 Commit Message Guidelines

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat:** New feature
- **fix:** Bug fix
- **docs:** Documentation changes
- **style:** Code style changes (formatting, etc.)
- **refactor:** Code refactoring
- **perf:** Performance improvements
- **test:** Adding or updating tests
- **chore:** Maintenance tasks

### Examples

```bash
# Good
feat(download): add support for 4K video downloads

Added support for downloading videos in 4K resolution.
Updated format selector to include 2160p option.

Closes #123

# Good
fix(ui): resolve glare effect not showing on mobile

The glare hover effect was not triggering on mobile devices.
Added touch event listeners to enable the effect on touch screens.

Fixes #456

# Bad
fixed stuff
updated code
changes
```

### Rules

- Use present tense ("add feature" not "added feature")
- Use imperative mood ("move cursor to..." not "moves cursor to...")
- First line max 72 characters
- Reference issues and PRs in footer

---

## 🧪 Testing

### Running Tests

```bash
# Run all tests
python test_app.py

# Run with coverage (if pytest-cov installed)
pytest --cov=app --cov-report=html

# Run specific test
python -m pytest test_app.py::test_function_name
```

### Writing Tests

```python
def test_download_video():
    """Test video download functionality."""
    # Arrange
    url = "https://www.youtube.com/watch?v=test"
    format = "mp4"
    
    # Act
    result = download_video(url, format)
    
    # Assert
    assert result["status"] == "success"
    assert "filename" in result
```

---

## 🏷️ Issue Labels

- **bug:** Something isn't working
- **enhancement:** New feature or request
- **documentation:** Documentation improvements
- **good first issue:** Good for newcomers
- **help wanted:** Extra attention needed
- **question:** Further information requested
- **wontfix:** This will not be worked on
- **duplicate:** This issue already exists

---

## 💬 Getting Help

- **Questions?** Open a discussion or issue
- **Need clarification?** Comment on the relevant issue/PR
- **Want to chat?** Reach out to the team (see README for contacts)

---

## 🎉 Recognition

Contributors will be:

- Listed in the project README
- Mentioned in release notes
- Given credit in commit history

---

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to YTDownloadX! 🚀

**Happy Coding!** 💻✨
