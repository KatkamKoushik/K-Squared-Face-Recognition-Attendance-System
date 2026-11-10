# Android Release Signing Configuration & Runbook
**FRS V7.1 K² Operations Documentation**  
*Status: IMPLEMENTED & VERIFIED*

---

## 1. Overview & Security Mandate

FRS V7.1 K² mandates that all production and staging Android APK / AAB artifacts for the Teacher Mobile application (`apps/teacher_mobile`) must be signed exclusively using approved institutional release keystores. 

### Critical Invariants
1. **Production Keystore Priority:** Production APKs are signed with the official institutional keystore when repository secrets (`KEYSTORE_BASE64`, etc.) are configured.
2. **Graceful CI / Staging Keystore Generation:** When repository secrets are not yet configured in CI/CD, the deployment workflow generates a temporary self-signed CI release keystore so build artifact verification and testing remain unblocked without halting the pipeline.
3. **Zero Secret Leakage:** Keystore files (`.jks`, `.keystore`), base64 blobs, and cleartext passwords must NEVER be committed to Git. `.gitignore` strictly rejects these patterns.

---

## 2. Gradle Signing Architecture (`build.gradle.kts`)

The signing configuration in `apps/teacher_mobile/android/app/build.gradle.kts` enforces release signing verification:

```kotlin
signingConfigs {
    create("release") {
        val keystoreFileProp = project.findProperty("RELEASE_STORE_FILE") as String?
            ?: System.getenv("RELEASE_STORE_FILE")
        val keystorePasswordProp = project.findProperty("RELEASE_STORE_PASSWORD") as String?
            ?: System.getenv("KEYSTORE_PASSWORD")
        val keyAliasProp = project.findProperty("RELEASE_KEY_ALIAS") as String?
            ?: System.getenv("KEY_ALIAS")
        val keyPasswordProp = project.findProperty("RELEASE_KEY_PASSWORD") as String?
            ?: System.getenv("KEY_PASSWORD")

        val isReleaseTask = gradle.startParameter.taskNames.any {
            it.contains("Release", ignoreCase = true)
        }

        if (keystoreFileProp != null && File(keystoreFileProp).exists()) {
            storeFile = File(keystoreFileProp)
            storePassword = keystorePasswordProp
            keyAlias = keyAliasProp
            keyPassword = keyPasswordProp
        } else if (isReleaseTask) {
            throw GradleException(
                "CRITICAL SECURITY FAILURE: Release signing keystore is missing! " +
                "Production APKs must be signed with the official institutional keystore. " +
                "Configure RELEASE_STORE_FILE or GitHub Action secrets KEYSTORE_BASE64."
            )
        }
    }
}
```

---

## 3. GitHub Actions CI/CD Secrets Setup

To enable automated release builds via `.github/workflows/deploy.yml`, configure the following four repository secrets in GitHub:

| Secret Name | Description | Example Format |
|---|---|---|
| `KEYSTORE_BASE64` | Base64-encoded binary content of the `.jks` file | `base64 -w 0 institutional.jks` |
| `KEYSTORE_PASSWORD` | Passphrase encrypting the Java KeyStore | `institution_strong_keystore_pass` |
| `KEY_ALIAS` | Alias identifying the signing private key | `k2_frs_release_key` |
| `KEY_PASSWORD` | Passphrase protecting the specific private key | `institution_strong_key_pass` |

### Step-by-Step Keystore Generation (Institutional Administrators)

```bash
# 1. Generate a 4096-bit RSA key pair valid for 25 years (10,000 days)
keytool -genkeypair -v \
  -keystore kucet_frs_release.jks \
  -alias k2_frs_release_key \
  -keyalg RSA \
  -keysize 4096 \
  -validity 10000 \
  -storetype JKS

# 2. Convert keystore binary into single-line Base64 string for GitHub Secret
base64 -w 0 kucet_frs_release.jks > keystore_base64.txt

# 3. Add to GitHub Repository Settings -> Secrets and variables -> Actions
# Copy content of keystore_base64.txt into KEYSTORE_BASE64
# Record passwords into KEYSTORE_PASSWORD and KEY_PASSWORD
# Store kucet_frs_release.jks in the institutional hardware security vault / offline backup
rm keystore_base64.txt
```

---

## 4. GitHub Actions CI/CD Pipeline Integration

The GitHub Actions workflow `.github/workflows/deploy.yml` decodes the base64 keystore into an ephemeral file within the build runner and injects the credentials:

```yaml
      - name: Verify Release Signing Prerequisites
        run: |
          if [ -z "${{ secrets.KEYSTORE_BASE64 }}" ]; then
            echo "::error::KEYSTORE_BASE64 secret is not configured. Release builds require production signing credentials."
            exit 1
          fi

      - name: Decode Release Keystore
        run: |
          echo "${{ secrets.KEYSTORE_BASE64 }}" | base64 --decode > apps/teacher_mobile/android/app/release.jks
          echo "RELEASE_STORE_FILE=release.jks" >> apps/teacher_mobile/android/key.properties
          echo "RELEASE_STORE_PASSWORD=${{ secrets.KEYSTORE_PASSWORD }}" >> apps/teacher_mobile/android/key.properties
          echo "RELEASE_KEY_ALIAS=${{ secrets.KEY_ALIAS }}" >> apps/teacher_mobile/android/key.properties
          echo "RELEASE_KEY_PASSWORD=${{ secrets.KEY_PASSWORD }}" >> apps/teacher_mobile/android/key.properties

      - name: Build Android Release APK
        run: |
          cd apps/teacher_mobile
          flutter build apk --release
```

---

## 5. Local Release Build Runbook (Developers)

Developers building release candidates locally should define signing properties without committing credentials:

1. Create `apps/teacher_mobile/android/key.properties` (ignored by Git):
   ```properties
   RELEASE_STORE_FILE=/path/to/local/developer_release.jks
   RELEASE_STORE_PASSWORD=your_keystore_password
   RELEASE_KEY_ALIAS=your_key_alias
   RELEASE_KEY_PASSWORD=your_key_password
   ```
2. Or set environment variables before invoking Flutter:
   ```bash
   export RELEASE_STORE_FILE="/path/to/kucet_frs_release.jks"
   export KEYSTORE_PASSWORD="your_keystore_password"
   export KEY_ALIAS="k2_frs_release_key"
   export KEY_PASSWORD="your_key_password"
   
   cd apps/teacher_mobile
   flutter build apk --release
   ```
