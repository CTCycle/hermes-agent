"""
Grailed.com signup using nodriver (undetected Chrome) - v2: aggressive submit strategies
"""
import asyncio
import json
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

# Safely encode for JS embedding
EMAIL_JS = json.dumps(EMAIL)
PASSWORD_JS = json.dumps(PASSWORD)

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
    
    await tab.get("https://www.grailed.com/")
    await tab.sleep(5)
    
    # Step 0: Accept cookies first (may interfere with interactions)
    print("\n=== Step 0: Accepting cookies ===")
    try:
        accept_btn = await tab.find("Accept All", best_match=True, timeout=5)
        await accept_btn.click()
        print("Clicked 'Accept All' cookies")
        await tab.sleep(2)
    except Exception as e:
        print(f"Cookie accept: {e}")
    
    await tab.save_screenshot(str(SCREENSHOT_DIR / "grailed_v2_01_initial.png"))
    page_text = await tab.evaluate("document.body.innerText", return_by_value=True)
    print(f"Page text (first 500):\n{page_text[:500]}")
    
    # Step 1: Click SIGN UP 
    print("\n=== Step 1: Clicking SIGN UP ===")
    try:
        signup_btn = await tab.find("SIGN UP", best_match=True, timeout=10)
        await signup_btn.click()
        print("Clicked SIGN UP")
    except Exception as e:
        print(f"Find+click SIGN UP failed: {e}")
        await tab.evaluate("""
            () => {
                const all = [...document.querySelectorAll('button, a, [role="button"]')];
                const btn = all.find(el => (el.textContent||'').trim().toUpperCase() === 'SIGN UP');
                if (btn) { btn.click(); return 'clicked'; }
                return 'not found';
            }
        """, return_by_value=True)
    
    await tab.sleep(5)
    
    # Step 2: Click "CREATE ACCOUNT WITH EMAIL" 
    print("\n=== Step 2: Clicking CREATE ACCOUNT WITH EMAIL ===")
    try:
        email_btn = await tab.find("CREATE ACCOUNT WITH EMAIL", best_match=True, timeout=10)
        await email_btn.click()
        print("Clicked CREATE ACCOUNT WITH EMAIL")
    except Exception as e:
        print(f"Find+click failed: {e}")
        result = await tab.evaluate("""
            () => {
                const all = [...document.querySelectorAll('button, a, [role="button"], div, span')];
                for (const el of all) {
                    const text = (el.textContent||'').trim().toUpperCase();
                    if (text.includes('CREATE') && text.includes('EMAIL')) {
                        el.click(); return 'clicked ' + el.tagName;
                    }
                }
                return 'not found';
            }
        """, return_by_value=True)
        print(f"JS: {result}")
    
    await tab.sleep(5)
    await tab.save_screenshot(str(SCREENSHOT_DIR / "grailed_v2_02_modal_open.png"))
    
    page_text = await tab.evaluate("document.body.innerText", return_by_value=True)
    print(f"Modal check (first 400):\n{page_text[:400]}")
    
    # Step 3: Fill form via JS using native value setter (tricks React)
    print("\n=== Step 3: Filling form ===")
    
    fill_js = f"""
        () => {{
            const emailVal = {EMAIL_JS};
            const passVal = {PASSWORD_JS};
            const inputs = document.querySelectorAll('input');
            let emailField = null, passField = null;
            
            for (const inp of inputs) {{
                const ph = (inp.placeholder || '').toLowerCase();
                const name = (inp.name || '').toLowerCase();
                const type = (inp.type || '').toLowerCase();
                const label = inp.labels && inp.labels[0] ? (inp.labels[0].textContent || '').toLowerCase() : '';
                
                if (type === 'email' || name === 'email' || ph.includes('email') || label.includes('email')) {{
                    emailField = inp;
                }}
                if (type === 'password' || name === 'password' || ph.includes('password') || label.includes('password')) {{
                    passField = inp;
                }}
            }}
            
            const nativeSetter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
            
            if (emailField) {{
                emailField.focus();
                nativeSetter.call(emailField, emailVal);
                emailField.dispatchEvent(new Event('input', {{bubbles: true}}));
                emailField.dispatchEvent(new Event('change', {{bubbles: true}}));
                emailField.dispatchEvent(new Event('blur', {{bubbles: true}}));
            }}
            
            if (passField) {{
                passField.focus();
                nativeSetter.call(passField, passVal);
                passField.dispatchEvent(new Event('input', {{bubbles: true}}));
                passField.dispatchEvent(new Event('change', {{bubbles: true}}));
                passField.dispatchEvent(new Event('blur', {{bubbles: true}}));
            }}
            
            return {{ 
                emailFound: !!emailField, 
                passFound: !!passField,
                emailValue: emailField ? emailField.value.substring(0, 10) + '...' : 'none',
                passLength: passField ? passField.value.length : 0
            }};
        }}
    """
    
    fill_result = await tab.evaluate(fill_js, return_by_value=True)
    print(f"Fill result: {fill_result}")
    
    await tab.sleep(2)
    await tab.save_screenshot(str(SCREENSHOT_DIR / "grailed_v2_03_form_filled.png"))
    
    # Step 4: Try multiple submit strategies
    print("\n=== Step 4: Submitting form ===")
    
    async def check_page_changed():
        url = await tab.evaluate("window.location.href", return_by_value=True)
        text = await tab.evaluate("document.body.innerText", return_by_value=True)
        changed = "SIGN UP" not in text[:500] or url != "https://www.grailed.com/"
        return changed, url, text[:300]
    
    submitted = False
    
    # Strategy 1: Press Enter on password field
    print("\n--- Strategy 1: Press Enter on password field ---")
    try:
        pass_field = await tab.select('input[type="password"]', timeout=5)
        await pass_field.focus()
        await pass_field.send_keys("\n")
        print("Sent Enter")
        await tab.sleep(5)
        changed, url, snippet = await check_page_changed()
        if changed:
            print(f"SUCCESS! URL: {url}, text: {snippet}")
            submitted = True
        else:
            print("No change detected")
    except Exception as e:
        print(f"Failed: {e}")
    
    if not submitted:
        # Strategy 2: form.submit()
        print("\n--- Strategy 2: form.submit() ---")
        result = await tab.evaluate("""
            () => {
                const pwField = document.querySelector('input[type="password"]');
                if (pwField && pwField.form) {
                    pwField.form.submit();
                    return 'submitted form';
                }
                const forms = document.querySelectorAll('form');
                for (const f of forms) {
                    if (f.querySelector('input[type="password"]')) {
                        f.submit();
                        return 'submitted form with password field';
                    }
                }
                return 'no form found';
            }
        """, return_by_value=True)
        print(f"Result: {result}")
        await tab.sleep(5)
        changed, url, snippet = await check_page_changed()
        if changed:
            print("SUCCESS!")
            submitted = True
        else:
            print("No change")
    
    if not submitted:
        # Strategy 3: Mouse events at coordinates
        print("\n--- Strategy 3: JS mouse events at coordinates ---")
        result = await tab.evaluate("""
            () => {
                const buttons = document.querySelectorAll('button');
                for (const btn of buttons) {
                    if ((btn.textContent||'').trim().toUpperCase() === 'SIGN UP') {
                        const rect = btn.getBoundingClientRect();
                        const cx = rect.left + rect.width / 2;
                        const cy = rect.top + rect.height / 2;
                        ['mousedown', 'mouseup', 'click'].forEach(eventType => {
                            btn.dispatchEvent(new MouseEvent(eventType, {
                                bubbles: true, cancelable: true,
                                clientX: cx, clientY: cy, button: 0, buttons: 1
                            }));
                        });
                        return `clicked at (${cx.toFixed(0)}, ${cy.toFixed(0)}) on ${btn.tagName}`;
                    }
                }
                return 'no button';
            }
        """, return_by_value=True)
        print(f"Result: {result}")
        await tab.sleep(5)
        changed, url, snippet = await check_page_changed()
        if changed:
            print("SUCCESS!")
            submitted = True
        else:
            print("No change")
    
    if not submitted:
        # Strategy 4: CDP Input.dispatchMouseEvent
        print("\n--- Strategy 4: CDP mouse click ---")
        try:
            coords = await tab.evaluate("""
                () => {
                    const buttons = document.querySelectorAll('button');
                    for (const btn of buttons) {
                        if ((btn.textContent||'').trim().toUpperCase() === 'SIGN UP') {
                            const r = btn.getBoundingClientRect();
                            return {x: Math.round(r.left + r.width/2), y: Math.round(r.top + r.height/2)};
                        }
                    }
                    return null;
                }
            """, return_by_value=True)
            
            if coords:
                print(f"Button at: ({coords['x']}, {coords['y']})")
                await tab.send(uc.cdp.input.dispatch_mouse_event(
                    type="mousePressed", x=coords['x'], y=coords['y'],
                    button="left", buttons=1, click_count=1
                ))
                await asyncio.sleep(0.15)
                await tab.send(uc.cdp.input.dispatch_mouse_event(
                    type="mouseReleased", x=coords['x'], y=coords['y'],
                    button="left", buttons=0, click_count=1
                ))
                print("CDP click dispatched")
                await tab.sleep(5)
                changed, url, snippet = await check_page_changed()
                if changed:
                    print("SUCCESS!")
                    submitted = True
                else:
                    print("No change")
        except Exception as e:
            print(f"Failed: {e}")
    
    if not submitted:
        # Strategy 5: React fiber onClick
        print("\n--- Strategy 5: React fiber onClick ---")
        result = await tab.evaluate("""
            () => {
                const buttons = document.querySelectorAll('button');
                for (const btn of buttons) {
                    if ((btn.textContent||'').trim().toUpperCase() !== 'SIGN UP') continue;
                    
                    // Try React fiber
                    const fiberKey = Object.keys(btn).find(k => k.startsWith('__reactFiber'));
                    if (fiberKey) {
                        let fiber = btn[fiberKey];
                        let depth = 0;
                        while (fiber && depth < 20) {
                            const props = fiber.memoizedProps || {};
                            if (props.onClick || props.onPress || props.onTap) {
                                const handler = props.onClick || props.onPress || props.onTap;
                                try { handler({preventDefault: ()=>{}, stopPropagation: ()=>{}}); } catch(e) {}
                                return 'triggered React fiber handler at depth ' + depth;
                            }
                            fiber = fiber.return;
                            depth++;
                        }
                    }
                    
                    // Try __reactEventHandlers
                    const ehKey = Object.keys(btn).find(k => k.startsWith('__reactEventHandlers') || k.startsWith('__reactProps'));
                    if (ehKey) {
                        const handlers = btn[ehKey];
                        const clickHandler = handlers.onClick || handlers.onPress || handlers.onTap;
                        if (clickHandler) {
                            try { clickHandler({preventDefault: ()=>{}, stopPropagation: ()=>{}}); } catch(e) {}
                            return 'triggered React eventHandlers onClick';
                        }
                    }
                    
                    // Try __reactInternalInstance
                    const riKey = Object.keys(btn).find(k => k.startsWith('__reactInternalInstance'));
                    if (riKey) {
                        let inst = btn[riKey];
                        let depth = 0;
                        while (inst && depth < 20) {
                            const props = inst.memoizedProps || inst.pendingProps || {};
                            if (props.onClick) {
                                try { props.onClick({preventDefault: ()=>{}, stopPropagation: ()=>{}}); } catch(e) {}
                                return 'triggered React internal onClick at depth ' + depth;
                            }
                            inst = inst.return;
                            depth++;
                        }
                    }
                    
                    return 'no React handlers found. Keys: ' + Object.keys(btn).filter(k => k.startsWith('__')).join(', ');
                }
                return 'no SIGN UP button';
            }
        """, return_by_value=True)
        print(f"Result: {result}")
        await tab.sleep(5)
        changed, url, snippet = await check_page_changed()
        if changed:
            print("SUCCESS!")
            submitted = True
        else:
            print("No change")
    
    # Final screenshots and check
    await tab.save_screenshot(str(SCREENSHOT_DIR / "grailed_v2_04_final.png"))
    
    current_url = await tab.evaluate("window.location.href", return_by_value=True)
    page_text = await tab.evaluate("document.body.innerText", return_by_value=True)
    print(f"\n=== FINAL STATE ===")
    print(f"URL: {current_url}")
    print(f"Page text (first 800):\n{page_text[:800]}")
    
    has_signup = "SIGN UP" in page_text.upper()
    print(f"\nSign Up still visible: {has_signup}")
    print(f"Submitted: {submitted}")
    
    if not submitted and has_signup:
        print("\n*** ALL STRATEGIES FAILED - keeping browser open for manual CAPTCHA/intervention ***")
        await asyncio.sleep(120)
    
    await tab.sleep(3)
    browser.stop()
    print("Browser closed.")


if __name__ == "__main__":
    asyncio.run(main())
