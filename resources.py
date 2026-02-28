# resources.py
# This file is auto-generated. Do not edit manually.
# It contains the legal text resources for the Klyve application.

EULA_TEXT = """KLYVE Open Source License
Version 1.1 (Open Source) | Last Updated: 28 February 2026

Copyright (c) 2026 Mario Joseph Lewis

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

SUPPLEMENTAL TERMS & DISCLOSURES
1. Brand and Trademark Ownership
The name "Klyve," the Klyve logo, and all associated branding elements are the exclusive intellectual property of Mario Joseph Lewis. While this license grants you the right to use and modify the source code, it does not grant permission to use the "Klyve" brand name, trademarks, or logos for any derivative works, redistributed versions, or commercial offerings without express written consent. Any modified version of this software must be rebranded under a different name.

2. Third-Party Dependencies & Credits
Klyve includes various third-party open-source components (e.g., PySide6/Qt, Shiboken6). These components are governed by their own respective licenses (such as LGPLv3). Full license texts and obligatory credits for these dependencies are available in the "About Klyve" menu and the root installation directory. Your use of this Software constitutes acceptance of these third-party terms.

3. AI Transparency (EU AI Act Article 50)
Klyve functions as an autonomous software development factory using generative AI.

Synthetic Generation: Code and architectural specifications produced are synthetically generated and not by a human.

Marking: The Developer reserves the right to embed machine-readable metadata within generated files to identify them as AI-synthesized for regulatory compliance.

4. User Responsibility
As an open-source tool for developers, you act as the "Human-in-the-Loop." You bear sole responsibility for reviewing, auditing, and testing all generated code before deployment.
"""

PRIVACY_POLICY_TEXT = """PRIVACY POLICY FOR KLYVE
Version 1.1 (Open Source) | Last Updated: 28 February 2026

1. THE "LOCAL-FIRST" PROMISE
I, Mario J. Lewis ("Developer"), believe your code and project data belong entirely to you. Klyve is designed as a Local-First application, ensuring that:

No Cloud Storage: The Developer does not operate any cloud servers to upload, store, or monitor your project source code, specifications, or planning documents.

Local Processing: All file generation, database management, and logic processing occur locally on your machine.

Direct Connection: When AI features are used, the Software connects directly from your machine to the AI provider (e.g., OpenAI, Google, Anthropic) using the API key you provide. Your data does not pass through any server owned or operated by the Developer.

2. DATA MINIMALISM
Since the Software runs locally, data collection is non-existent to minimal:

No Telemetry: This version of the Software does not collect usage data, tracking metrics, or background telemetry.

Crash Reports: If you voluntarily submit a bug report via email or the repository, the Developer receives only the data you choose to include (e.g., logs, screenshots).

Website Data: Accessing the Klyve website or GitHub repository results in standard web server logs (IP address, browser type) collected by the hosting provider for security and download tracking.

Transparency Metadata: To comply with regulatory requirements (e.g., EU AI Act), machine-readable metadata indicating that files are AI-generated may be embedded within created files. This metadata does not contain personally identifiable information (PII).

3. THIRD-PARTY AI PROVIDERS
The Software functions by transmitting data to third-party Large Language Model (LLM) providers based on your configuration.

Data Transmitted: Code snippets, file structures, and documentation from your active project are sent to the provider you select.

Model Training: The Developer does not access or store this data and cannot use it to train or fine-tune proprietary models.

Provider Policies: Whether a third-party provider uses your data for training depends on your specific agreement and API tier with them. You are responsible for reviewing the data usage policies of providers like OpenAI, Google, or Anthropic.

API Keys: Your API keys are stored locally in an encrypted database on your machine. The Developer cannot access or revoke them.

4. YOUR DATA RIGHTS
Because the Developer does not store your personal project data, "Right to Access" or "Right to Delete" requests do not apply to the Developer's infrastructure.

Project Control: You possess all project data on your local machine and can delete it at any time.

Key Management: You maintain full control over your API keys within the Software's settings.

5. GOVERNING LAW
This Privacy Policy and your use of the Software are governed by the laws of India. Any disputes arising from this policy shall be subject to the exclusive jurisdiction of the courts in Bangalore, Karnataka, India."""

THIRD_PARTY_NOTICES_TEXT = """KLYVE Open Source License

Copyright (c) 2026 Mario Joseph Lewis    

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:    

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.    

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.    

SUPPLEMENTAL TERMS & DISCLOSURES
1. Brand and Name Ownership
The name "Klyve," the Klyve logo, and all associated branding elements are the exclusive intellectual property of Mario Joseph Lewis. While this license grants you the right to use and modify the source code, it does not grant permission to use the "Klyve" name or branding for any derivative works, redistributed versions, or commercial offerings. Any modified version of this software must be clearly rebranded under a different name.   

2. Third-Party Dependencies & Credits
Klyve includes various third-party open-source components (e.g., PySide6/Qt, Shiboken6). These components are governed by their own respective licenses (such as LGPLv3). Full license texts and obligatory credits are available in the "About Klyve" menu and the root installation directory. Your use of this Software constitutes acceptance of these third-party terms.   

3. AI Transparency (EU AI Act Article 50)
Klyve functions as an autonomous software development factory using generative AI.   


Synthetic Generation: Code and architectural specifications produced are synthetically generated and not by a human.   


Marking: The Developer reserves the right to embed machine-readable metadata within generated files to identify them as AI-synthesized for regulatory compliance.   

4. User Responsibility
As an open-source tool for developers, you act as the "Human-in-the-Loop". You bear sole responsibility for reviewing, auditing, and testing all generated code before deployment. The Developer assumes no liability for damage resulting from the use of the Software.   

2. Updated Privacy Policy
1. LOCAL-FIRST COMMITMENT
Klyve is designed as a Local-First application. Your code and project data belong entirely to you.   


No Cloud Storage: The Developer (Mario J. Lewis) does not operate cloud servers to store your source code or specifications.   


Local Processing: All generation and logic processing occur locally on your machine.   


Direct Connection: AI features connect directly from your machine to your chosen AI provider using your own API keys. Data does not pass through any server owned by the Developer.   

2. DATA TRANSMISSION TO AI PROVIDERS
To function, the Software transmits project-related snippets and logs to the third-party Large Language Model (LLM) provider configured in your settings.   


Training: The Developer does not access your data and cannot use it to train proprietary models.   


Third-Party Policies: Whether your data is used for training by the LLM provider depends on your separate agreement and API tier with that provider.   

3. MINIMAL DATA COLLECTION


Telemetry: This version does not collect telemetry or usage data.   


API Keys: Keys are stored locally in an encrypted database on your machine. The Developer cannot access them.   

4. GOVERNING LAW
This policy and the use of the Software are governed by the laws of India, with exclusive jurisdiction in Bangalore, Karnataka, India."""
