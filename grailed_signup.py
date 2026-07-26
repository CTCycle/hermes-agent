"""
Grailed.com signup using nodriver (undetected Chrome)
Run with: bws run --project-id 5a118425-239e-4d77-8ca8-b48000e0707e -- python3 grailed_signup.py
"""
import asyncio
import os
import sys
from pathlib import Path

import nodriver as uc

EMAIL = os.environ.get("CARTEL_777_GRAILED_EMAIL", "cartel777.shop@proton.me")
PASSWORD = os.environ.get("CARTEL_777_GRAILED_PASSWORD", "")
SCREENSHOT_DIR = Path("G:/Playground/Hermes/hermes-agent/screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

if not PASSWORD:
    print("ERROR: No password found in env vars!")
    sys.exit(1)

print(f"Email: {EMAIL}")
print(f"Password length: {len(PASSWORD)}")


async def main():
    print("Starting nodriver browser...")
    browser = await uc.start(
        headless=False,
        browser_args=[
            "--no-sandbox",
            "--disable-blink-features=AutomationControlled",
            "--window-size=1280,900",
        ],
    )
    
    tab = browser.main_tab
    print("Browser started. Navigating to grailed.com...")
    
    # Navigate
    await tab.get("https://www.grailed.com/")
    await tab.sleep(5)
    
    # Screenshot 1
    await tab.save_screenshot(str(SCREENSHOT_DIR / "grailed_01_initial.png"))
    print("Screenshot 1: Initial page")
    
    # Dump page text to understand what's there
    page_text = await tab.evaluate("document.body.innerText", return_by_value=True)
    print(f"Page text (first 800 chars):\n{page_text[:800]}")
    
    # Step 1: Click SIGN UP button using tab.find (text-based)
    print("\n=== Step 1: Finding and clicking SIGN UP ===")
    try:
        signup_btn = await tab.find("SIGN UP", best_match=True, timeout=10)
        print(f"Found SIGN UP: tag={signup_btn.tag_name if hasattr(signup_btn, 'tag_name') else '?'}")
        await signup_btn.click()
        print("Clicked SIGN UP")
    except Exception as e:
        print(f"tab.find('SIGN UP') failed: {e}")
        # Try JS click as fallback
        result = await tab.evaluate("""
            () => {
                const all = document.querySelectorAll('button, a, [role="button"]');
                for (const el of all) {
                    const text = (el.textContent || '').trim().toUpperCase();
                    if (text === 'SIGN UP') { el.click(); return 'clicked SIGN UP button'; }
                }
                // Try any element
                const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_ELEMENT);
                let node;
                while (node = walker.nextNode()) {
                    if (node.children.length === 0 && (node.textContent || '').trim().toUpperCase() === 'SIGN UP') {
                        node.click();
                        return 'clicked SIGN UP on ' + node.tagName;
                    }
                }
                return 'NOT FOUND';
            }
        """, return_by_value=True)
        print(f"JS fallback: {result}")
    
    await tab.sleep(5)
    await tab.save_screenshot(str(SCREENSHOT_DIR / "grailed_02_after_signup_click.png"))
    print("Screenshot 2: After SIGN UP click")
    
    # Check what appeared
    page_text = await tab.evaluate("document.body.innerText", return_by_value=True)
    print(f"\nPage text after SIGN UP click (first 800):\n{page_text[:800]}")
    
    # Step 2: Click "CREATE ACCOUNT WITH EMAIL" 
    print("\n=== Step 2: Finding CREATE ACCOUNT WITH EMAIL ===")
    try:
        email_btn = await tab.find("CREATE ACCOUNT WITH EMAIL", best_match=True, timeout=10)
        print(f"Found CREATE ACCOUNT WITH EMAIL")
        await email_btn.click()
        print("Clicked CREATE ACCOUNT WITH EMAIL")
    except Exception as e:
        print(f"tab.find('CREATE ACCOUNT WITH EMAIL') failed: {e}")
        # Try partial match
        try:
            email_btn = await tab.find("CREATE ACCOUNT", best_match=True, timeout=5)
            await email_btn.click()
            print("Clicked via 'CREATE ACCOUNT' partial match")
        except Exception as e2:
            print(f"Partial match also failed: {e2}")
            # JS fallback
            result = await tab.evaluate("""
                () => {
                    const all = document.querySelectorAll('button, a, [role="button"], div');
                    for (const el of all) {
                        const text = (el.textContent || '').trim().toUpperCase();
                        if (text.includes('CREATE') && text.includes('EMAIL')) {
                            el.click(); return 'clicked: ' + el.tagName + ' ' + el.textContent.trim().substring(0,50);
                        }
                    }
                    return 'NOT FOUND';
                }
            """, return_by_value=True)
            print(f"JS fallback: {result}")
    
    await tab.sleep(5)
    await tab.save_screenshot(str(SCREENSHOT_DIR / "grailed_03_after_email_click.png"))
    print("Screenshot 3: After email signup click")
    
    # Check form state
    page_text = await tab.evaluate("document.body.innerText", return_by_value=True)
    print(f"\nPage text after email click (first 800):\n{page_text[:800]}")
    
    # Step 3: Fill email and password
    print("\n=== Step 3: Filling form ===")
    
    # Find email input
    email_field = None
    try:
        email_field = await tab.select('input[type="email"]', timeout=5)
        print("Found email input by type=email")
    except Exception:
        pass
    
    if not email_field:
        try:
            email_field = await tab.select('input[name="email"]', timeout=3)
            print("Found email input by name=email")
        except Exception:
            pass
    
    if not email_field:
        # Use JS to find and fill
        print("Using JS to find all inputs and fill email...")
        result = await tab.evaluate(f"""
            () => {{
                const inputs = document.querySelectorAll('input');
                for (const inp of inputs) {{
                    const attrs = [];
                    for (const attr of inp.attributes) attrs.push(attr.name + '=' + attr.value);
                    console.log('Input:', inp.type, inp.name, inp.placeholder, attrs.join(', '));
                    if (inp.type === 'email' || inp.name === 'email' || (inp.placeholder || '').toLowerCase().includes('email')) {{
                        inp.focus();
                        inp.value = '{EMAIL}';
                        inp.dispatchEvent(new Event('input', {{bubbles: true}}));
                        inp.dispatchEvent(new Event('change', {{bubbles: true}}));
                        return 'filled email: type=' + inp.type + ' name=' + inp.name;
                    }}
                }}
                // Last resort: first visible text input
                for (const inp of inputs) {{
                    if ((inp.type === 'text' || inp.type === 'email' || !inp.type) && inp.offsetParent !== null) {{
                        inp.value = '{EMAIL}';
                        inp.dispatchEvent(new Event('input', {{bubbles: true}}));
                        return 'filled first visible input: type=' + inp.type;
                    }}
                }}
                return 'NO INPUTS FOUND';
            }}
        """, return_by_value=True)
        print(f"JS email fill: {result}")
    else:
        await email_field.click()
        await email_field.send_keys(EMAIL)
        print("Filled email via send_keys")
    
    await tab.sleep(1)
    
    # Find password input
    pass_field = None
    try:
        pass_field = await tab.select('input[type="password"]', timeout=5)
        print("Found password input by type=password")
    except Exception:
        try:
            pass_field = await tab.select('input[name="password"]', timeout=3)
            print("Found password input by name=password")
        except Exception:
            pass
    
    if not pass_field:
        print("Using JS to fill password...")
        result = await tab.evaluate(f"""
            () => {{
                const inputs = document.querySelectorAll('input');
                for (const inp of inputs) {{
                    if (inp.type === 'password') {{
                        inp.focus();
                        inp.value = '{PASSWORD}';
                        inp.dispatchEvent(new Event('input', {{bubbles: true}}));
                        inp.dispatchEvent(new Event('change', {{bubbles: true}}));
                        return 'filled password';
                    }}
                }}
                return 'NO PASSWORD FIELD';
            }}
        """, return_by_value=True)
        print(f"JS password fill: {result}")
    else:
        await pass_field.click()
        await pass_field.send_keys(PASSWORD)
        print("Filled password via send_keys")
    
    await tab.sleep(2)
    await tab.save_screenshot(str(SCREENSHOT_DIR / "grailed_04_form_filled.png"))
    print("Screenshot 4: Form filled")
    
    # Step 4: Submit
    print("\n=== Step 4: Submitting form ===")
    
    # Try to find submit button by text
    submitted = False
    for btn_text in ["SIGN UP", "Sign Up", "Create Account", "CREATE ACCOUNT", "Submit", "Continue", "Register", "SIGN UP FOR GRAILED"]:
        try:
            btn = await tab.find(btn_text, best_match=True, timeout=3)
            print(f"Found submit button: '{btn_text}'")
            await btn.click()
            submitted = True
            print(f"Clicked '{btn_text}'")
            break
        except Exception:
            continue
    
    if not submitted:
        # Try CSS selectors for submit
        for sel in ['button[type="submit"]', 'input[type="submit"]', 'form button']:
            try:
                btn = await tab.select(sel, timeout=3)
                print(f"Found submit via selector: {sel}")
                await btn.click()
                submitted = True
                break
            except Exception:
                continue
    
    if not submitted:
        # JS fallback
        print("Using JS to submit...")
        result = await tab.evaluate("""
            () => {
                // Try pressing Enter on password field
                const pwField = document.querySelector('input[type="password"]');
                if (pwField) {
                    pwField.form && pwField.form.submit();
                    return 'submitted form';
                }
                // Try clicking any button with signup-related text
                const buttons = document.querySelectorAll('button, [role="button"], input[type="submit"]');
                for (const btn of buttons) {
                    const text = (btn.textContent || btn.value || '').toUpperCase();
                    if (text.includes('SIGN') || text.includes('CREATE') || text.includes('REGISTER') || text.includes('SUBMIT') || text.includes('CONTINUE')) {
                        btn.click();
                        return 'clicked: ' + text.substring(0, 40);
                    }
                }
                return 'NO SUBMIT FOUND';
            }
        """, return_by_value=True)
        print(f"JS submit: {result}")
    
    await tab.sleep(8)
    await tab.save_screenshot(str(SCREENSHOT_DIR / "grailed_05_after_submit.png"))
    print("Screenshot 5: After submit")
    
    # Step 5: Check results
    print("\n=== Step 5: Checking results ===")
    
    current_url = await tab.evaluate("window.location.href", return_by_value=True)
    print(f"Current URL: {current_url}")
    
    page_text = await tab.evaluate("document.body.innerText", return_by_value=True)
    print(f"Page text (first 1000):\n{page_text[:1000]}")
    
    # Success checks
    success_keywords = [
        "successfully created", "welcome", "verify your email", 
        "check your email", "confirmation", "account created",
        "logout", "sign out", "my account", "profile"
    ]
    found_success = []
    for kw in success_keywords:
        if kw.lower() in page_text.lower():
            found_success.append(kw)
    
    if found_success:
        print(f"SUCCESS INDICATORS: {found_success}")
    else:
        print("No clear success indicators found")
    
    # Check for error messages
    error_keywords = ["error", "invalid", "already exists", "try again", "failed"]
    found_errors = []
    for kw in error_keywords:
        if kw.lower() in page_text.lower():
            found_errors.append(kw)
    if found_errors:
        print(f"ERROR INDICATORS: {found_errors}")
    
    # Is SIGN UP still visible? (If yes, probably not logged in)
    has_signup = "SIGN UP" in page_text.upper()
    print(f"'SIGN UP' still visible: {has_signup}")
    
    # Look for any user/profile links
    profile_info = await tab.evaluate("""
        () => {
            const links = document.querySelectorAll('a[href*="profile"], a[href*="account"], a[href*="/users/"]');
            const results = [];
            for (const l of links) {
                results.push({text: l.textContent.trim(), href: l.href});
            }
            return results;
        }
    """, return_by_value=True)
    print(f"Profile/account links: {profile_info}")
    
    # Final screenshot
    await tab.save_screenshot(str(SCREENSHOT_DIR / "grailed_06_final.png"))
    print(f"\nAll screenshots saved in: {SCREENSHOT_DIR}")
    
    # Check for CAPTCHA
    captcha_indicators = ["captcha", "recaptcha", "hcaptcha", "verify you are human", "not a robot"]
    has_captcha = any(kw.lower() in page_text.lower() for kw in captcha_indicators)
    if has_captcha:
        print("\n!!! CAPTCHA DETECTED - manual intervention may be needed !!!")
        print("Keeping browser open for manual CAPTCHA solving...")
        # Keep browser open so user can solve captcha
        await asyncio.sleep(120)
    
    print("\nDone. Browser stays open for 30s...")
    await tab.sleep(30)
    
    browser.stop()
    print("Browser closed.")


if __name__ == "__main__":
    asyncio.run(main())
