import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Optional
import re

def analyze_project_structure(project_path: Path) -> Dict:
    """
    Analyzes the project directory structure and collects comprehensive information.
    
    Args:
        project_path: Path to the project folder
        
    Returns:
        dict: Project analysis data
    """
    analysis = {
        'project_name': project_path.name,
        'total_files': 0,
        'total_lines': 0,
        'file_types': {},
        'languages': set(),
        'directories': [],
        'main_files': [],
        'dependencies': {},
        'structure': [],
        'config_files': [],
        'test_files': 0,
        'doc_files': []
    }
    
    # Enhanced language detection
    language_map = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.jsx': 'React (JSX)',
        '.tsx': 'React (TypeScript)',
        '.java': 'Java',
        '.cpp': 'C++',
        '.c': 'C',
        '.h': 'C/C++ Header',
        '.cs': 'C#',
        '.php': 'PHP',
        '.rb': 'Ruby',
        '.go': 'Go',
        '.rs': 'Rust',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.scala': 'Scala',
        '.r': 'R',
        '.m': 'MATLAB/Objective-C',
        '.lua': 'Lua',
        '.pl': 'Perl',
        '.sh': 'Shell Script',
        '.bash': 'Bash',
        '.html': 'HTML',
        '.css': 'CSS',
        '.scss': 'SCSS',
        '.sass': 'Sass',
        '.less': 'Less',
        '.sql': 'SQL',
        '.vue': 'Vue.js',
        '.svelte': 'Svelte',
        '.dart': 'Dart',
        '.xml': 'XML',
        '.json': 'JSON',
        '.yaml': 'YAML',
        '.yml': 'YAML',
        '.md': 'Markdown',
        '.tex': 'LaTeX'
    }
    
    # Comprehensive dependency/config files
    dependency_files = {
        'requirements.txt': 'Python',
        'setup.py': 'Python',
        'pyproject.toml': 'Python',
        'Pipfile': 'Python',
        'environment.yml': 'Conda',
        'package.json': 'Node.js',
        'package-lock.json': 'Node.js',
        'yarn.lock': 'Yarn',
        'pnpm-lock.yaml': 'pnpm',
        'Gemfile': 'Ruby',
        'Gemfile.lock': 'Ruby',
        'pom.xml': 'Maven (Java)',
        'build.gradle': 'Gradle (Java)',
        'Cargo.toml': 'Rust',
        'go.mod': 'Go',
        'go.sum': 'Go',
        'composer.json': 'PHP',
        'Podfile': 'iOS/CocoaPods',
        'pubspec.yaml': 'Dart/Flutter'
    }
    
    config_files = [
        '.gitignore', '.dockerignore', 'Dockerfile', 'docker-compose.yml',
        '.env.example', '.eslintrc', '.prettierrc', 'tsconfig.json',
        'webpack.config.js', 'vite.config.js', '.babelrc', 'jest.config.js',
        'pytest.ini', 'tox.ini', '.flake8', 'mypy.ini', 'setup.cfg'
    ]
    
    # Scan project directory
    for item in project_path.rglob('*'):
        # Skip common ignore folders
        if any(part in ['.git', 'node_modules', '__pycache__', 'venv', '.venv', 
                       'dist', 'build', 'target', '.idea', '.vscode', 'coverage'] 
               for part in item.parts):
            continue
        
        if item.is_file():
            analysis['total_files'] += 1
            
            # Count lines of code
            try:
                with open(item, 'r', encoding='utf-8', errors='ignore') as f:
                    analysis['total_lines'] += sum(1 for _ in f)
            except:
                pass
            
            # Count file types
            ext = item.suffix.lower()
            if ext:
                analysis['file_types'][ext] = analysis['file_types'].get(ext, 0) + 1
                
                # Detect languages
                if ext in language_map:
                    analysis['languages'].add(language_map[ext])
            
            # Check for test files
            if 'test' in item.name.lower() or item.parent.name.lower() in ['tests', 'test', '__tests__']:
                analysis['test_files'] += 1
            
            # Check for documentation
            if ext in ['.md', '.rst', '.txt'] and item.name.upper() not in ['LICENSE', 'README.MD']:
                analysis['doc_files'].append(item.name)
            
            # Check for dependency files
            if item.name in dependency_files:
                analysis['main_files'].append(item.name)
                extract_dependencies(item, analysis, dependency_files[item.name])
            
            # Check for config files
            if item.name in config_files or item.name.startswith('.env'):
                analysis['config_files'].append(item.name)
        
        elif item.is_dir() and item.parent == project_path:
            analysis['directories'].append(item.name)
    
    # Create structure overview (exclude output files)
    for item in sorted(project_path.iterdir()):
        if item.name.startswith('.') or item.name in ['node_modules', '__pycache__', 'venv', '.venv']:
            continue
        
        # Skip obvious output/scan files
        if re.match(r'.*_\d{8}_\d{6}\.(csv|json|txt)$', item.name):
            continue
        
        if item.is_dir():
            file_count = sum(1 for _ in item.rglob('*') if _.is_file() and 
                           not any(x in _.parts for x in ['node_modules', '__pycache__', 'venv']))
            analysis['structure'].append(f"{item.name}/ ({file_count} files)")
        else:
            analysis['structure'].append(item.name)
    
    analysis['languages'] = sorted(list(analysis['languages']))
    
    return analysis


def extract_dependencies(file_path: Path, analysis: Dict, tech: str) -> None:
    """Extract dependencies from various dependency files."""
    try:
        if file_path.name == 'requirements.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                deps = [line.strip().split('==')[0].split('>=')[0].split('~=')[0] 
                       for line in f if line.strip() and not line.startswith('#')]
                analysis['dependencies'][tech] = deps[:15]
        
        elif file_path.name == 'package.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
                analysis['dependencies'][tech] = list(deps.keys())[:15]
                
                # Extract scripts
                if 'scripts' in data:
                    analysis['npm_scripts'] = data['scripts']
        
        elif file_path.name == 'Cargo.toml':
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                deps = re.findall(r'^(\w+)\s*=', content, re.MULTILINE)
                analysis['dependencies'][tech] = deps[:15]
        
        elif file_path.name in ['Gemfile', 'pyproject.toml', 'go.mod']:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if file_path.name == 'pyproject.toml':
                    deps = re.findall(r'([a-zA-Z0-9_-]+)\s*[=~>]', content)
                else:
                    deps = re.findall(r'^\s*(?:gem|require)\s+["\']([^"\']+)', content, re.MULTILINE)
                analysis['dependencies'][tech] = deps[:15]
                
    except Exception as e:
        print(f"  ⚠️  Could not parse {file_path.name}: {e}")


def read_sample_code(project_path: Path, max_files: int = 3) -> List[Dict]:
    """
    Reads sample code files from the project.
    """
    code_samples = []
    code_extensions = ['.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', 
                      '.c', '.go', '.rs', '.rb', '.php', '.vue', '.swift']
    
    count = 0
    for ext in code_extensions:
        if count >= max_files:
            break
        
        for file in project_path.rglob(f'*{ext}'):
            if any(part in file.parts for part in ['node_modules', '__pycache__', 'venv', '.venv', 'dist', 'build']):
                continue
            
            # Prioritize main/index files
            if file.stem not in ['main', 'index', 'app'] and count > 0:
                continue
            
            try:
                with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if 100 < len(content) < 10000:  # Reasonable file size
                        code_samples.append({
                            'filename': file.name,
                            'relative_path': str(file.relative_to(project_path)),
                            'language': ext[1:],
                            'content': content[:1500]
                        })
                        count += 1
                        
                        if count >= max_files:
                            break
            except:
                continue
    
    return code_samples


def detect_project_type(analysis: Dict) -> str:
    """Detect the type of project based on files and structure."""
    files = set(analysis['main_files'] + analysis['config_files'])
    
    if 'package.json' in files:
        if any('react' in str(dep).lower() for deps in analysis.get('dependencies', {}).values() for dep in deps):
            return 'React Application'
        elif any('vue' in str(dep).lower() for deps in analysis.get('dependencies', {}).values() for dep in deps):
            return 'Vue.js Application'
        elif any('express' in str(dep).lower() for deps in analysis.get('dependencies', {}).values() for dep in deps):
            return 'Node.js/Express Backend'
        elif any('next' in str(dep).lower() for deps in analysis.get('dependencies', {}).values() for dep in deps):
            return 'Next.js Application'
        return 'Node.js Application'
    
    if 'requirements.txt' in files or 'setup.py' in files or 'pyproject.toml' in files:
        if any('django' in str(dep).lower() for deps in analysis.get('dependencies', {}).values() for dep in deps):
            return 'Django Application'
        elif any('flask' in str(dep).lower() for deps in analysis.get('dependencies', {}).values() for dep in deps):
            return 'Flask Application'
        elif any('fastapi' in str(dep).lower() for deps in analysis.get('dependencies', {}).values() for dep in deps):
            return 'FastAPI Application'
        return 'Python Project'
    
    if 'Cargo.toml' in files:
        return 'Rust Project'
    
    if 'go.mod' in files:
        return 'Go Project'
    
    if 'pom.xml' in files or 'build.gradle' in files:
        return 'Java Project'
    
    return 'Software Project'


def load_auto_generated_info(project_path: Path) -> Optional[Dict]:
    """Load automatically generated README info if available."""
    info_file = project_path / 'readme_info.json'
    
    if info_file.exists():
        try:
            with open(info_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    return None


def get_user_input(project_path: Path) -> Dict:
    """
    Prompts user for README details.
    Can use auto-generated information as defaults.
    
    Returns:
        dict: User-provided information
    """
    # Check for auto-generated info
    auto_info = load_auto_generated_info(project_path)
    
    if auto_info:
        print("\n" + "=" * 70)
        print("🤖 AUTO-GENERATED INFO FOUND!".center(70))
        print("=" * 70)
        print("\nWould you like to:")
        print("  1. Use auto-generated information (recommended)")
        print("  2. Enter information manually")
        print("  3. Use auto-generated with manual edits")
        
        choice = input("\nYour choice (1-3, default: 1): ").strip() or '1'
        
        if choice == '1':
            print("\n✅ Using auto-generated information!")
            return auto_info
        elif choice == '3':
            print("\n✏️  You can press Enter to keep auto-generated values")
    
    print("\n" + "=" * 70)
    print("📝 PROJECT INFORMATION".center(70))
    print("=" * 70)
    print("\nPlease provide the following details for your README:")
    print("(Press Enter to skip optional fields)\n")
    
    user_data = {}
    
    # Helper function to get input with default
    def get_with_default(prompt: str, default: str = '') -> str:
        if default:
            result = input(f"{prompt} [{default}]: ").strip()
            return result if result else default
        return input(f"{prompt}: ").strip()
    
    # Get defaults from auto_info if available
    defaults = auto_info if auto_info and choice == '3' else {}
    
    # Project description
    user_data['description'] = get_with_default(
        "📋 Project description (1-2 sentences)", 
        defaults.get('description', '')
    )
    
    # Features
    print("\n✨ Key features (enter one per line, empty line to finish):")
    if defaults.get('features'):
        print("   Auto-detected features:")
        for i, feat in enumerate(defaults['features'][:5], 1):
            print(f"   {i}. {feat}")
        use_auto = input("\n   Use these features? (Y/n): ").strip().lower()
        if use_auto != 'n':
            user_data['features'] = defaults['features']
        else:
            features = []
            i = 1
            while True:
                feature = input(f"   Feature {i}: ").strip()
                if not feature:
                    break
                features.append(feature)
                i += 1
            user_data['features'] = features
    else:
        features = []
        i = 1
        while True:
            feature = input(f"   Feature {i}: ").strip()
            if not feature:
                break
            features.append(feature)
            i += 1
        user_data['features'] = features
    
    # Usage instructions
    print("\n💻 Usage/Run instructions:")
    user_data['run_command'] = get_with_default(
        "   Main command to run the project",
        defaults.get('run_command', '')
    )
    user_data['additional_usage'] = get_with_default(
        "   Additional usage notes (optional)",
        defaults.get('additional_usage', '')
    )
    
    # Installation notes
    user_data['install_notes'] = get_with_default(
        "\n📦 Any special installation notes? (optional)",
        defaults.get('install_notes', '')
    )
    
    # Author info
    print("\n👤 Author Information:")
    user_data['author_name'] = get_with_default(
        "   Your name",
        defaults.get('author_name', 'Your Name')
    )
    user_data['github_username'] = get_with_default(
        "   GitHub username",
        defaults.get('github_username', 'yourusername')
    )
    user_data['email'] = get_with_default(
        "   Email (optional)",
        defaults.get('email', '')
    )
    
    # Repository info
    user_data['repo_name'] = get_with_default(
        "\n🔗 GitHub repository name (optional)",
        defaults.get('repo_name', '')
    )
    
    # License
    print("\n📄 License:")
    if defaults.get('license'):
        print(f"   Auto-detected: {defaults['license']}")
        keep_license = input("   Keep this license? (Y/n): ").strip().lower()
        if keep_license != 'n':
            user_data['license'] = defaults['license']
        else:
            print("   1. MIT")
            print("   2. Apache 2.0")
            print("   3. GPL-3.0")
            print("   4. BSD-3-Clause")
            print("   5. Other/None")
            license_choice = input("   Choose license (1-5): ").strip()
            license_map = {
                '1': 'MIT', '2': 'Apache-2.0', '3': 'GPL-3.0',
                '4': 'BSD-3-Clause', '5': 'See LICENSE file'
            }
            user_data['license'] = license_map.get(license_choice, 'MIT')
    else:
        print("   1. MIT")
        print("   2. Apache 2.0")
        print("   3. GPL-3.0")
        print("   4. BSD-3-Clause")
        print("   5. Other/None")
        license_choice = input("   Choose license (1-5, default: 1): ").strip()
        license_map = {
            '1': 'MIT', '2': 'Apache-2.0', '3': 'GPL-3.0',
            '4': 'BSD-3-Clause', '5': 'See LICENSE file'
        }
        user_data['license'] = license_map.get(license_choice, 'MIT')
    
    # Screenshots/demo
    if defaults.get('has_screenshots'):
        print(f"\n📸 Screenshots detected in project")
        user_data['has_screenshots'] = True
        user_data['screenshot_note'] = input("   Screenshot filename or path: ").strip() or 'screenshots/demo.png'
    else:
        user_data['has_screenshots'] = input("\n📸 Do you have screenshots to add? (y/N): ").strip().lower() == 'y'
        if user_data['has_screenshots']:
            user_data['screenshot_note'] = input("   Screenshot filename or note: ").strip()
    
    # Acknowledgments
    user_data['acknowledgments'] = get_with_default(
        "\n🙏 Any acknowledgments? (optional)",
        defaults.get('acknowledgments', '')
    )
    
    return user_data


def generate_readme_content(analysis: Dict, code_samples: List[Dict], user_data: Dict) -> str:
    """
    Generates comprehensive README content based on project analysis and user input.
    """
    project_type = detect_project_type(analysis)
    project_name = analysis['project_name']
    
    # Build README
    readme = f"# {project_name}\n\n"
    
    # Add description
    if user_data.get('description'):
        readme += f"> {user_data['description']}\n\n"
    
    # Badges
    readme += "[![License](https://img.shields.io/badge/License-{license}-blue.svg)](LICENSE)\n".format(
        license=user_data.get('license', 'MIT').replace('-', '--'))
    
    if user_data.get('github_username') and user_data.get('repo_name'):
        repo = user_data['repo_name']
        username = user_data['github_username']
        readme += f"[![GitHub Stars](https://img.shields.io/github/stars/{username}/{repo}?style=social)](https://github.com/{username}/{repo})\n"
    
    if 'Python' in analysis['languages']:
        readme += "![Python](https://img.shields.io/badge/Python-3.x-blue.svg)\n"
    if any(lang in analysis['languages'] for lang in ['JavaScript', 'React (JSX)', 'TypeScript']):
        readme += "![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-yellow.svg)\n"
    
    readme += "\n"
    
    # Table of Contents
    readme += """## 📑 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technologies Used](#technologies-used)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
"""
    
    if code_samples:
        readme += "- [Code Examples](#code-examples)\n"
    if analysis['dependencies']:
        readme += "- [Dependencies](#dependencies)\n"
    
    readme += """- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

"""
    
    # Overview
    readme += "## 📊 Overview\n\n"
    if user_data.get('description'):
        readme += f"{user_data['description']}\n\n"
    
    readme += f"This {project_type.lower()} contains **{analysis['total_files']} files** "
    readme += f"with approximately **{analysis['total_lines']:,} lines of code**.\n\n"
    
    # Screenshots
    if user_data.get('has_screenshots'):
        readme += "### 📸 Screenshots\n\n"
        if user_data.get('screenshot_note'):
            readme += f"![Screenshot]({user_data['screenshot_note']})\n\n"
        else:
            readme += "<!-- Add your screenshots here -->\n"
            readme += "![Screenshot](path/to/screenshot.png)\n\n"
    
    # Features
    readme += "## ✨ Features\n\n"
    if user_data.get('features'):
        for feature in user_data['features']:
            readme += f"- ✅ {feature}\n"
    else:
        readme += "- Feature 1: Describe your main feature\n"
        readme += "- Feature 2: Another key feature\n"
        readme += "- Feature 3: Additional functionality\n"
    readme += "\n"
    
    # Technologies
    if analysis['languages']:
        readme += "## 🛠️ Technologies Used\n\n"
        for lang in analysis['languages']:
            readme += f"- **{lang}**\n"
        readme += "\n"
    
    # Installation
    readme += "## 🚀 Installation\n\n"
    readme += "### Prerequisites\n\n"
    
    if 'Python' in analysis['languages']:
        readme += "- Python 3.8 or higher\n"
    if any(lang in analysis['languages'] for lang in ['JavaScript', 'TypeScript', 'React (JSX)']):
        readme += "- Node.js 14.x or higher\n"
    if 'Rust' in analysis['languages']:
        readme += "- Rust 1.60 or higher\n"
    if 'Go' in analysis['languages']:
        readme += "- Go 1.18 or higher\n"
    
    if user_data.get('install_notes'):
        readme += f"- {user_data['install_notes']}\n"
    
    readme += "\n### Setup\n\n"
    
    # Repository clone
    if user_data.get('github_username') and user_data.get('repo_name'):
        repo_url = f"https://github.com/{user_data['github_username']}/{user_data['repo_name']}.git"
    else:
        repo_url = f"https://github.com/yourusername/{project_name}.git"
    
    readme += f"""1. Clone the repository:
```bash
git clone {repo_url}
cd {project_name}
```

"""
    
    if 'requirements.txt' in analysis['main_files']:
        readme += """2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

"""
    
    if 'package.json' in analysis['main_files']:
        readme += """2. Install dependencies:
```bash
npm install
# or
yarn install
```

"""
    
    # Usage
    readme += "## 💻 Usage\n\n"
    
    if user_data.get('run_command'):
        readme += f"Run the project:\n\n```bash\n{user_data['run_command']}\n```\n\n"
    
    if user_data.get('additional_usage'):
        readme += f"{user_data['additional_usage']}\n\n"
    
    if analysis.get('npm_scripts'):
        readme += "### Available Scripts\n\n"
        for script, command in list(analysis['npm_scripts'].items())[:5]:
            readme += f"- `npm run {script}` - {command}\n"
        readme += "\n"
    
    # Project structure
    if analysis['structure']:
        readme += "## 📁 Project Structure\n\n```\n"
        readme += f"{project_name}/\n"
        for item in analysis['structure'][:15]:
            readme += f"├── {item}\n"
        if len(analysis['structure']) > 15:
            readme += f"└── ...and {len(analysis['structure']) - 15} more\n"
        readme += "```\n\n"
    
    # Code examples
    if code_samples:
        readme += "## 📝 Code Examples\n\n"
        for sample in code_samples[:2]:
            readme += f"### `{sample['relative_path']}`\n\n"
            readme += f"```{sample['language']}\n{sample['content'][:600]}\n"
            if len(sample['content']) > 600:
                readme += "# ...\n"
            readme += "```\n\n"
    
    # Dependencies
    if analysis['dependencies']:
        readme += "## 📦 Dependencies\n\n"
        for tech, deps in analysis['dependencies'].items():
            readme += f"### {tech}\n\n"
            for dep in deps[:10]:
                readme += f"- `{dep}`\n"
            if len(deps) > 10:
                readme += f"- *...and {len(deps) - 10} more*\n"
            readme += "\n"
    
    # Testing
    if analysis['test_files'] > 0:
        readme += f"""## 🧪 Testing

This project includes **{analysis['test_files']} test file(s)**.

```bash
# Run tests (adjust command as needed)
pytest  # For Python
# or
npm test  # For Node.js
```

"""
    
    # Contributing
    readme += """## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

Please make sure to update tests as appropriate and follow the existing code style.

"""
    
    # License
    readme += f"""## 📄 License

This project is licensed under the {user_data.get('license', 'MIT')} License - see the [LICENSE](LICENSE) file for details.

"""
    
    # Contact
    readme += f"""## 👤 Contact

**{user_data.get('author_name', 'Your Name')}**

- GitHub: [@{user_data.get('github_username', 'yourusername')}](https://github.com/{user_data.get('github_username', 'yourusername')})
"""
    
    if user_data.get('email'):
        readme += f"- Email: {user_data['email']}\n"
    
    readme += "\n"
    
    # Acknowledgments
    if user_data.get('acknowledgments'):
        readme += f"""## 🙏 Acknowledgments

{user_data['acknowledgments']}

"""
    
    # Support
    readme += """## ⭐ Show your support

Give a ⭐️ if this project helped you!

"""
    
    readme += f"\n---\n\n*📅 Generated on {datetime.now().strftime('%B %d, %Y')}*\n"
    
    return readme


def create_readme(project_path: str, output_file: str = 'README.md', 
                 include_samples: bool = True, interactive: bool = True) -> Optional[Path]:
    """
    Main function to analyze project and create README.
    """
    project_path = Path(project_path).resolve()
    
    if not project_path.exists():
        print(f"❌ Error: Project folder '{project_path}' does not exist.")
        return None
    
    if not project_path.is_dir():
        print(f"❌ Error: '{project_path}' is not a directory.")
        return None
    
    print("\n" + "=" * 70)
    print("📚 README GENERATOR".center(70))
    print("=" * 70)
    print(f"\n🔍 Analyzing project: {project_path.name}")
    print("-" * 70)
    
    # Analyze project
    print("📊 Analyzing project structure...")
    analysis = analyze_project_structure(project_path)
    
    print(f"  ✓ Found {analysis['total_files']} files")
    print(f"  ✓ Total lines of code: {analysis['total_lines']:,}")
    print(f"  ✓ Detected languages: {', '.join(analysis['languages']) if analysis['languages'] else 'None detected'}")
    print(f"  ✓ Configuration files: {len(analysis['config_files'])}")
    print(f"  ✓ Test files: {analysis['test_files']}")
    
    # Read sample code
    code_samples = []
    if include_samples:
        print("\n📄 Reading sample code files...")
        code_samples = read_sample_code(project_path)
        print(f"  ✓ Collected {len(code_samples)} code samples")
    
    # Get user input
    user_data = {}
    if interactive:
        user_data = get_user_input(project_path)
    
    # Generate README
    print("\n✍️  Generating README content...")
    readme_content = generate_readme_content(analysis, code_samples, user_data)
    
    # Save README
    output_path = project_path / output_file
    
    # Backup existing README
    if output_path.exists():
        backup_path = project_path / f"README.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        print(f"\n⚠️  Backing up existing README to: {backup_path.name}")
        try:
            output_path.rename(backup_path)
        except Exception as e:
            print(f"  ❌ Could not create backup: {e}")
            return None
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
    except Exception as e:
        print(f"\n❌ Error writing README: {e}")
        return None
    
    print(f"\n✅ README.md created successfully!")
    print("-" * 70)
    print("\n📋 Summary:")
    print(f"  • Project: {analysis['project_name']}")
    print(f"  • Type: {detect_project_type(analysis)}")
    print(f"  • Files: {analysis['total_files']}")
    print(f"  • Lines of code: {analysis['total_lines']:,}")
    print(f"  • Languages: {', '.join(analysis['languages']) if analysis['languages'] else 'None'}")
    print(f"  • Output: {output_path}")
    print("\n💡 Next steps:")
    print("  1. Review the generated README")
    print("  2. Add screenshots if you mentioned them")
    print("  3. Update any placeholder text")
    print("  4. Commit and push to your repository")
    print("\n" + "=" * 70 + "\n")
    
    return output_path


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("📚 AUTOMATED README GENERATOR".center(70))
    print("=" * 70)
    print("\n✨ This script will:")
    print("  • Analyze your complete project structure")
    print("  • Detect programming languages and frameworks")
    print("  • Extract dependencies and configurations")
    print("  • Collect project information from you")
    print("  • Generate a comprehensive, professional README.md")
    print("\n" + "-" * 70)
    
    # Interactive mode
    project_folder = input("\n📂 Enter the path to your project folder: ").strip()
    
    if not project_folder:
        print("❌ No path provided. Exiting.")
    else:
        # Remove quotes if user wrapped path in quotes
        project_folder = project_folder.strip('"\'')
        
        # Ask for options
        print("\n⚙️  Options:")
        include_code = input("Include code samples in README? (Y/n): ").strip().lower() != 'n'
        interactive = input("Enter project details interactively? (Y/n): ").strip().lower() != 'n'
        
        result = create_readme(project_folder, include_samples=include_code, interactive=interactive)
        
        if result:
            print(f"🎉 Success! Your README is ready at: {result}")
        else:
            print("❌ README generation failed. Please check the errors above.")