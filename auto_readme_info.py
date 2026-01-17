import os
import re
import ast
import json
from pathlib import Path
from typing import Dict, List, Optional, Set
import configparser

class AutoReadmeInfoGenerator:
    """
    Automatically generates README information by analyzing project code and files.
    Works with readme_generator.py to provide smart defaults.
    """
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path).resolve()
        self.project_name = self.project_path.name
        self.analysis = {}
        
    def analyze_project(self) -> Dict:
        """Main analysis function that gathers all project information."""
        print("\n🔍 Analyzing project automatically...")
        
        info = {
            'description': self._generate_description(),
            'features': self._extract_features(),
            'run_command': self._detect_run_command(),
            'additional_usage': self._detect_usage_info(),
            'install_notes': self._detect_install_notes(),
            'author_name': self._detect_author_name(),
            'github_username': self._detect_github_username(),
            'email': self._detect_email(),
            'repo_name': self._detect_repo_name(),
            'license': self._detect_license(),
            'has_screenshots': self._detect_screenshots(),
            'screenshot_note': '',
            'acknowledgments': self._detect_acknowledgments()
        }
        
        return info
    
    def _read_file_safe(self, filepath: Path, max_lines: int = 500) -> str:
        """Safely read file content."""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = [next(f) for _ in range(max_lines) if f]
                return ''.join(lines)
        except:
            return ""
    
    def _find_main_files(self) -> List[Path]:
        """Find main Python files in the project."""
        main_files = []
        
        # Priority patterns for main files
        priority_patterns = [
            'main.py', 'app.py', 'run.py', 'server.py', 
            'index.py', '__main__.py', 'manage.py'
        ]
        
        for pattern in priority_patterns:
            found = list(self.project_path.glob(pattern))
            if found:
                main_files.extend(found)
        
        # If no main files found, get all .py files
        if not main_files:
            main_files = [f for f in self.project_path.glob('*.py') 
                         if not f.name.startswith('_') and f.name != 'setup.py'][:5]
        
        return main_files
    
    def _generate_description(self) -> str:
        """Generate project description from docstrings, comments, and filenames."""
        description_sources = []
        
        # Check for existing README
        for readme in ['README.md', 'README.txt', 'readme.md']:
            readme_path = self.project_path / readme
            if readme_path.exists():
                content = self._read_file_safe(readme_path, 20)
                # Extract first meaningful paragraph
                lines = [l.strip() for l in content.split('\n') if l.strip() and not l.startswith('#')]
                if lines:
                    description_sources.append(lines[0][:200])
        
        # Check main Python files for module docstrings
        for py_file in self._find_main_files():
            content = self._read_file_safe(py_file, 50)
            
            # Extract module docstring
            try:
                tree = ast.parse(content)
                docstring = ast.get_docstring(tree)
                if docstring:
                    # Get first sentence or two
                    sentences = docstring.split('.')[:2]
                    desc = '. '.join(s.strip() for s in sentences if s.strip()) + '.'
                    description_sources.append(desc)
            except:
                # Fallback: look for triple-quoted strings at the start
                match = re.search(r'^["\'{3}](.*?)["\'{3}]', content, re.MULTILINE | re.DOTALL)
                if match:
                    desc = match.group(1).strip().split('\n')[0]
                    description_sources.append(desc)
        
        # Check package.json description
        package_json = self.project_path / 'package.json'
        if package_json.exists():
            try:
                with open(package_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'description' in data:
                        description_sources.append(data['description'])
            except:
                pass
        
        # Check setup.py
        setup_py = self.project_path / 'setup.py'
        if setup_py.exists():
            content = self._read_file_safe(setup_py)
            match = re.search(r'description\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                description_sources.append(match.group(1))
        
        # Analyze project name and files to generate description
        if not description_sources:
            description_sources.append(self._infer_from_structure())
        
        # Return the best description
        return description_sources[0] if description_sources else f"A {self.project_name} project"
    
    def _infer_from_structure(self) -> str:
        """Infer project purpose from structure and filenames."""
        files = [f.name.lower() for f in self.project_path.rglob('*.py') if f.is_file()]
        
        keywords = {
            'web': ['flask', 'django', 'fastapi', 'app', 'server', 'api', 'route'],
            'data': ['data', 'analysis', 'pandas', 'numpy', 'visualization', 'plot'],
            'ml': ['model', 'train', 'predict', 'neural', 'learning', 'ai'],
            'automation': ['script', 'automate', 'bot', 'scrape', 'crawler'],
            'network': ['network', 'scan', 'socket', 'connection', 'ping'],
            'gui': ['gui', 'tkinter', 'qt', 'window', 'interface'],
            'cli': ['cli', 'command', 'terminal', 'argparse'],
            'game': ['game', 'player', 'score', 'pygame'],
            'security': ['security', 'encrypt', 'decrypt', 'hash', 'auth']
        }
        
        detected = []
        for category, terms in keywords.items():
            if any(term in ' '.join(files) for term in terms):
                detected.append(category)
        
        if 'network' in detected and 'scan' in ' '.join(files):
            return "A network scanning and analysis tool"
        elif 'web' in detected:
            return "A web application built with modern frameworks"
        elif 'data' in detected:
            return "A data analysis and visualization tool"
        elif 'ml' in detected:
            return "A machine learning application"
        elif 'automation' in detected:
            return "An automation script for streamlining tasks"
        elif detected:
            return f"A {detected[0]} application"
        else:
            return f"A Python-based {self.project_name} application"
    
    def _extract_features(self) -> List[str]:
        """Extract features from code analysis."""
        features = []
        
        # Analyze main Python files
        for py_file in self._find_main_files():
            content = self._read_file_safe(py_file)
            
            # Look for function definitions (potential features)
            func_pattern = r'def\s+([a-z_][a-z0-9_]*)\s*\('
            functions = re.findall(func_pattern, content)
            
            # Filter out private functions and common ones
            public_funcs = [f for f in functions 
                          if not f.startswith('_') 
                          and f not in ['main', 'run', 'setup', 'init']]
            
            # Convert function names to features
            for func in public_funcs[:5]:
                # Convert snake_case to readable text
                readable = func.replace('_', ' ').title()
                features.append(readable)
        
        # Look for class definitions
        for py_file in self._find_main_files():
            content = self._read_file_safe(py_file)
            class_pattern = r'class\s+([A-Z][a-zA-Z0-9]*)'
            classes = re.findall(class_pattern, content)
            
            for cls in classes[:3]:
                # Convert class name to feature
                # CamelCase to readable
                readable = re.sub(r'([A-Z])', r' \1', cls).strip()
                features.append(f"{readable} implementation")
        
        # Check for specific patterns in code
        all_content = ' '.join(self._read_file_safe(f) for f in self._find_main_files())
        
        feature_indicators = {
            'export': 'Data export to multiple formats',
            'import': 'Data import from various sources',
            'csv': 'CSV file processing',
            'json': 'JSON data handling',
            'api': 'RESTful API integration',
            'database': 'Database connectivity',
            'threading': 'Multi-threaded processing',
            'async': 'Asynchronous operations',
            'logging': 'Comprehensive logging system',
            'config': 'Configurable settings',
            'cli': 'Command-line interface',
            'gui': 'Graphical user interface',
            'report': 'Report generation',
            'scan': 'Network/system scanning',
            'monitor': 'Real-time monitoring',
            'visualization': 'Data visualization'
        }
        
        for keyword, feature in feature_indicators.items():
            if keyword in all_content.lower() and feature not in features:
                features.append(feature)
        
        # If no features found, add generic ones
        if not features:
            features = [
                "Core functionality implementation",
                "Easy-to-use interface",
                "Extensible architecture"
            ]
        
        return features[:8]  # Limit to 8 features
    
    def _detect_run_command(self) -> str:
        """Detect the command to run the project."""
        
        # Check for package.json scripts
        package_json = self.project_path / 'package.json'
        if package_json.exists():
            try:
                with open(package_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'scripts' in data:
                        if 'start' in data['scripts']:
                            return 'npm start'
                        elif 'dev' in data['scripts']:
                            return 'npm run dev'
            except:
                pass
        
        # Check for Python main files
        main_patterns = ['main.py', 'app.py', 'run.py', '__main__.py', 'manage.py']
        for pattern in main_patterns:
            if (self.project_path / pattern).exists():
                if pattern == 'manage.py':
                    return 'python manage.py runserver'
                return f'python {pattern}'
        
        # Check if any Python file has __main__ block
        for py_file in self.project_path.glob('*.py'):
            content = self._read_file_safe(py_file, 100)
            if 'if __name__' in content:
                return f'python {py_file.name}'
        
        # Check for setup.py (installable package)
        if (self.project_path / 'setup.py').exists():
            return 'python setup.py install && ' + self.project_name.lower()
        
        return 'python main.py  # Adjust as needed'
    
    def _detect_usage_info(self) -> str:
        """Detect additional usage information."""
        usage_info = []
        
        # Check for argparse or click usage
        for py_file in self._find_main_files():
            content = self._read_file_safe(py_file)
            
            if 'argparse' in content or 'ArgumentParser' in content:
                usage_info.append("Run with --help to see all available options")
            
            if 'click' in content:
                usage_info.append("Use --help flag for command documentation")
            
            # Look for configuration files
            if 'config' in content.lower():
                usage_info.append("Configure settings in the config file before running")
        
        return ' | '.join(usage_info) if usage_info else ''
    
    def _detect_install_notes(self) -> str:
        """Detect special installation requirements."""
        notes = []
        
        # Check requirements.txt for system dependencies
        req_file = self.project_path / 'requirements.txt'
        if req_file.exists():
            content = self._read_file_safe(req_file)
            
            if 'opencv' in content.lower():
                notes.append("OpenCV system libraries required")
            if 'psycopg2' in content.lower():
                notes.append("PostgreSQL development headers needed")
            if 'mysqlclient' in content.lower():
                notes.append("MySQL development libraries required")
            if 'scapy' in content.lower():
                notes.append("May require root/admin privileges for network scanning")
        
        # Check for Docker
        if (self.project_path / 'Dockerfile').exists():
            notes.append("Docker available for containerized deployment")
        
        # Check for environment variables
        env_example = self.project_path / '.env.example'
        if env_example.exists() or (self.project_path / '.env').exists():
            notes.append("Copy .env.example to .env and configure environment variables")
        
        return ' | '.join(notes) if notes else ''
    
    def _detect_author_name(self) -> str:
        """Detect author name from git config or setup.py."""
        
        # Check git config
        git_config = self.project_path / '.git' / 'config'
        if git_config.exists():
            try:
                config = configparser.ConfigParser()
                config.read(git_config)
                if 'user' in config and 'name' in config['user']:
                    return config['user']['name']
            except:
                pass
        
        # Check setup.py
        setup_py = self.project_path / 'setup.py'
        if setup_py.exists():
            content = self._read_file_safe(setup_py)
            match = re.search(r'author\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                return match.group(1)
        
        # Check package.json
        package_json = self.project_path / 'package.json'
        if package_json.exists():
            try:
                with open(package_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'author' in data:
                        if isinstance(data['author'], str):
                            return data['author']
                        elif isinstance(data['author'], dict):
                            return data['author'].get('name', '')
            except:
                pass
        
        return os.getenv('USER', os.getenv('USERNAME', 'Your Name'))
    
    def _detect_github_username(self) -> str:
        """Detect GitHub username from git remote."""
        
        git_config = self.project_path / '.git' / 'config'
        if git_config.exists():
            content = self._read_file_safe(git_config)
            
            # Look for GitHub remote URL
            patterns = [
                r'github\.com[:/]([^/]+)/',
                r'url\s*=\s*https://github\.com/([^/]+)',
                r'url\s*=\s*git@github\.com:([^/]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, content)
                if match:
                    return match.group(1)
        
        return 'yourusername'
    
    def _detect_email(self) -> str:
        """Detect email from git config or setup.py."""
        
        # Check git config
        git_config = self.project_path / '.git' / 'config'
        if git_config.exists():
            try:
                config = configparser.ConfigParser()
                config.read(git_config)
                if 'user' in config and 'email' in config['user']:
                    return config['user']['email']
            except:
                pass
        
        # Check setup.py
        setup_py = self.project_path / 'setup.py'
        if setup_py.exists():
            content = self._read_file_safe(setup_py)
            match = re.search(r'author_email\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                return match.group(1)
        
        # Check package.json
        package_json = self.project_path / 'package.json'
        if package_json.exists():
            try:
                with open(package_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'author' in data and isinstance(data['author'], dict):
                        return data['author'].get('email', '')
            except:
                pass
        
        return ''
    
    def _detect_repo_name(self) -> str:
        """Detect repository name from git remote or project name."""
        
        git_config = self.project_path / '.git' / 'config'
        if git_config.exists():
            content = self._read_file_safe(git_config)
            
            # Extract repo name from URL
            match = re.search(r'github\.com[:/][^/]+/([^/\s]+?)(?:\.git)?(?:\s|$)', content)
            if match:
                return match.group(1)
        
        return self.project_name
    
    def _detect_license(self) -> str:
        """Detect license from LICENSE file."""
        
        license_files = ['LICENSE', 'LICENSE.txt', 'LICENSE.md', 'license', 'license.txt']
        
        for lic_file in license_files:
            lic_path = self.project_path / lic_file
            if lic_path.exists():
                content = self._read_file_safe(lic_path, 20).lower()
                
                if 'mit license' in content:
                    return 'MIT'
                elif 'apache' in content and '2.0' in content:
                    return 'Apache-2.0'
                elif 'gnu general public license' in content:
                    if 'version 3' in content:
                        return 'GPL-3.0'
                    elif 'version 2' in content:
                        return 'GPL-2.0'
                elif 'bsd' in content:
                    return 'BSD-3-Clause'
        
        return 'MIT'  # Default
    
    def _detect_screenshots(self) -> bool:
        """Check if screenshots directory exists."""
        
        screenshot_dirs = ['screenshots', 'images', 'docs/images', 'assets/images']
        
        for dir_name in screenshot_dirs:
            dir_path = self.project_path / dir_name
            if dir_path.exists() and dir_path.is_dir():
                # Check for image files
                image_files = list(dir_path.glob('*.png')) + list(dir_path.glob('*.jpg'))
                if image_files:
                    return True
        
        return False
    
    def _detect_acknowledgments(self) -> str:
        """Generate acknowledgments based on dependencies."""
        
        acks = []
        
        # Check requirements.txt for major frameworks
        req_file = self.project_path / 'requirements.txt'
        if req_file.exists():
            content = self._read_file_safe(req_file).lower()
            
            frameworks = {
                'flask': 'Flask framework',
                'django': 'Django framework',
                'fastapi': 'FastAPI framework',
                'numpy': 'NumPy library',
                'pandas': 'Pandas library',
                'tensorflow': 'TensorFlow',
                'pytorch': 'PyTorch',
                'scikit-learn': 'Scikit-learn'
            }
            
            for framework, name in frameworks.items():
                if framework in content:
                    acks.append(f"Built with {name}")
        
        # Check package.json
        package_json = self.project_path / 'package.json'
        if package_json.exists():
            try:
                with open(package_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    deps = data.get('dependencies', {})
                    
                    if 'react' in deps:
                        acks.append("Built with React")
                    if 'vue' in deps:
                        acks.append("Built with Vue.js")
                    if 'express' in deps:
                        acks.append("Powered by Express.js")
            except:
                pass
        
        return ' • '.join(acks) if acks else ''
    
    def save_to_file(self, info: Dict, output_file: str = 'readme_info.json'):
        """Save the generated info to a JSON file."""
        output_path = self.project_path / output_file
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(info, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Auto-generated info saved to: {output_path}")
        return output_path
    
    def display_summary(self, info: Dict):
        """Display a summary of the generated information."""
        print("\n" + "=" * 70)
        print("📋 AUTO-GENERATED README INFORMATION".center(70))
        print("=" * 70)
        
        print(f"\n📝 Description:")
        print(f"   {info['description']}")
        
        print(f"\n✨ Features ({len(info['features'])} detected):")
        for i, feature in enumerate(info['features'][:5], 1):
            print(f"   {i}. {feature}")
        if len(info['features']) > 5:
            print(f"   ...and {len(info['features']) - 5} more")
        
        print(f"\n💻 Run Command:")
        print(f"   {info['run_command']}")
        
        if info['additional_usage']:
            print(f"\n📖 Usage Notes:")
            print(f"   {info['additional_usage']}")
        
        if info['install_notes']:
            print(f"\n📦 Installation Notes:")
            print(f"   {info['install_notes']}")
        
        print(f"\n👤 Author Information:")
        print(f"   Name: {info['author_name']}")
        print(f"   GitHub: @{info['github_username']}")
        if info['email']:
            print(f"   Email: {info['email']}")
        
        print(f"\n🔗 Repository:")
        print(f"   {info['repo_name']}")
        
        print(f"\n📄 License:")
        print(f"   {info['license']}")
        
        print(f"\n📸 Screenshots:")
        print(f"   {'Available' if info['has_screenshots'] else 'Not detected'}")
        
        if info['acknowledgments']:
            print(f"\n🙏 Acknowledgments:")
            print(f"   {info['acknowledgments']}")
        
        print("\n" + "=" * 70)


def main():
    """Main function to run the auto-generator."""
    print("\n" + "=" * 70)
    print("🤖 AUTOMATIC README INFO GENERATOR".center(70))
    print("=" * 70)
    print("\n✨ This script will automatically:")
    print("  • Analyze your project code and structure")
    print("  • Extract descriptions from docstrings and comments")
    print("  • Detect features from function and class definitions")
    print("  • Identify run commands and usage patterns")
    print("  • Find author info from git config")
    print("  • Detect license and dependencies")
    print("  • Generate comprehensive project information")
    print("\n" + "-" * 70)
    
    project_folder = input("\n📂 Enter the path to your project folder: ").strip()
    
    if not project_folder:
        print("❌ No path provided. Exiting.")
        return
    
    # Remove quotes
    project_folder = project_folder.strip('"\'')
    
    # Create generator
    generator = AutoReadmeInfoGenerator(project_folder)
    
    # Analyze project
    info = generator.analyze_project()
    
    # Display summary
    generator.display_summary(info)
    
    # Ask to save
    save = input("\n💾 Save this information to readme_info.json? (Y/n): ").strip().lower()
    if save != 'n':
        generator.save_to_file(info)
        print("\n💡 You can now:")
        print("  1. Review and edit readme_info.json")
        print("  2. Run readme_generator.py and it will use this data")
        print("  3. Or manually use the information above")
    
    print("\n🎉 Done!\n")


if __name__ == "__main__":
    main()