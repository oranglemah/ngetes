#!/usr/bin/env python3
"""
K12 Teacher Verification - CLI Version
Flow sama persis dengan bot Telegram, tapi pakai input()/print() di Termux
"""

import asyncio
import httpx
import re
import os
import random
from datetime import datetime, timedelta
from document_generator import (
    generate_faculty_id,
    generate_pay_stub,
    generate_employment_letter,
    image_to_bytes,
)

# =====================================================
# KONFIGURASI
# =====================================================
SHEERID_BASE_URL = "https://services.sheerid.com"
ORGSEARCH_URL = "https://orgsearch.sheerid.net/rest/organization/search"

# Simpan data user (mirip user_data di bot)
user_data = {}


# =====================================================
# HELPER PRINT
# =====================================================

def line():
    print("=" * 60)


def prompt(text):
    print(text, end="")
    return input().strip()


# =====================================================
# SCHOOL SEARCH FUNCTIONS (SAMA DENGAN BOT)
# =====================================================

async def search_schools(query: str) -> list:
    """
    Search schools menggunakan SheerID Organization Search API
    Mencari K12 dan HIGH_SCHOOL schools
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        all_schools = []

        for school_type in ["K12", "HIGH_SCHOOL"]:
            try:
                params = {
                    "country": "US",
                    "type": school_type,
                    "name": query,
                }

                print(f"\n📡 Searching {school_type} schools...")
                print(f"Query: {query}")

                resp = await client.get(ORGSEARCH_URL, params=params)

                if resp.status_code != 200:
                    print(f"❌ API error for {school_type}: {resp.status_code}")
                    print(resp.text[:200])
                    continue

                data = resp.json()
                if not isinstance(data, list):
                    print(f"❌ API return bukan list untuk {school_type}")
                    continue

                print(f"✅ {school_type}: Found {len(data)} schools")
                all_schools.extend(data)

            except Exception as e:
                print(f"❌ Error searching {school_type}: {e}")
                continue

        # Remove duplicates berdasarkan ID
        seen_ids = set()
        unique_schools = []
        for school in all_schools:
            school_id = school.get("id")
            if school_id and school_id not in seen_ids:
                seen_ids.add(school_id)
                unique_schools.append(school)

                name = school.get("name", "Unknown")
                s_type = school.get("type", "N/A")
                city = school.get("city", "N/A")
                state = school.get("state", "N/A")
                print(f"  ✓ {name} ({s_type}) - {city}, {state}")

        print(f"\n📊 Total unique schools: {len(unique_schools)}")
        return unique_schools[:20]


def display_schools_cli(schools: list, school_query: str, user_id: int):
    """
    Tampilkan hasil search sekolah di terminal
    Mirip display_schools() tapi pakai print + input
    """
    print()
    line()
    print("🏫 SCHOOL SEARCH RESULTS")
    line()
    print(f"Query : {school_query}")
    print(f"Found : {len(schools)} schools\n")

    for idx, school in enumerate(schools):
        user_data[user_id][f"school_{idx}"] = school

        name = school.get("name", "Unknown")
        city = school.get("city", "")
        state = school.get("state", "")
        school_type = school.get("type", "SCHOOL")

        location = f"{city}, {state}" if city and state else state or "US"

        print(f"{idx+1}. {name}")
        print(f"   📍 {location}")
        print(f"   └─ Type: {school_type}\n")

    while True:
        choice = prompt("👉 Pilih nomor sekolah (1 - %d): " % len(schools))
        if not choice.isdigit():
            print("❌ Harus angka.")
            continue
        choice_int = int(choice)
        if 1 <= choice_int <= len(schools):
            return choice_int - 1
        else:
            print("❌ Nomor di luar range.")


# =====================================================
# SHEERID SUBMISSION (SAMA LOGIKA DENGAN BOT)
# =====================================================

async def submit_sheerid(
    verification_id: str,
    first_name: str,
    last_name: str,
    email: str,
    school: dict,
    pdf_data: bytes,
    png_data: bytes,
) -> dict:
    """
    Submit verification ke SheerID API
    Multi-step process:
    1. Submit personal info
    2. Skip SSO
    3. Request upload URLs
    4. Upload documents to S3
    5. Complete upload
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            print("\n🚀 Starting SheerID submission...")
            print(f"Verification ID: {verification_id}")

            age = random.randint(25, 60)
            birth_date = (datetime.now() - timedelta(days=age * 365)).strftime(
                "%Y-%m-%d"
            )
            device_fp = "".join(
                random.choice("0123456789abcdef") for _ in range(32)
            )

            # STEP 2: Submit personal info
            step2_url = (
                f"{SHEERID_BASE_URL}/rest/v2/verification/"
                f"{verification_id}/step/collectTeacherPersonalInfo"
            )
            step2_body = {
                "firstName": first_name,
                "lastName": last_name,
                "birthDate": birth_date,
                "email": email,
                "organization": {
                    "id": int(school["id"]),
                    "name": school["name"],
                },
                "deviceFingerprintHash": device_fp,
                "locale": "en-US",
            }

            print("\n📝 Step 2: Submitting personal info...")
            step2_resp = await client.post(step2_url, json=step2_body)
            if step2_resp.status_code != 200:
                msg = f"Step 2 failed: {step2_resp.status_code}"
                print("❌", msg)
                print(step2_resp.text[:300])
                return {"success": False, "message": msg}

            print("✅ Step 2 success")

            # STEP 3: Skip SSO
            print("\n🔄 Step 3: Skipping SSO...")
            sso_resp = await client.delete(
                f"{SHEERID_BASE_URL}/rest/v2/verification/"
                f"{verification_id}/step/sso"
            )
            print(f"✅ Step 3 success (status {sso_resp.status_code})")

            # STEP 4: Request upload URLs
            step4_url = (
                f"{SHEERID_BASE_URL}/rest/v2/verification/"
                f"{verification_id}/step/docUpload"
            )
            step4_body = {
                "files": [
                    {
                        "fileName": "paystub.pdf",
                        "mimeType": "application/pdf",
                        "fileSize": len(pdf_data),
                    },
                    {
                        "fileName": "faculty_id.png",
                        "mimeType": "image/png",
                        "fileSize": len(png_data),
                    },
                ]
            }

            print("\n📤 Step 4: Requesting upload URLs...")
            step4_resp = await client.post(step4_url, json=step4_body)
            if step4_resp.status_code != 200:
                msg = f"Step 4 failed: {step4_resp.status_code}"
                print("❌", msg)
                print(step4_resp.text[:300])
                return {"success": False, "message": msg}

            step4_data = step4_resp.json()
            documents = step4_data.get("documents", [])
            if len(documents) < 2:
                msg = "No upload URLs received from SheerID"
                print("❌", msg)
                return {"success": False, "message": msg}

            print(f"✅ Step 4 success: received {len(documents)} URLs")

            # STEP 5: Upload to S3
            print("\n☁️ Step 5: Uploading documents to S3...")

            pdf_url = documents[0]["uploadUrl"]
            pdf_upload = await client.put(
                pdf_url,
                content=pdf_data,
                headers={"Content-Type": "application/pdf"},
            )
            print(f"  ✓ PDF uploaded: {pdf_upload.status_code}")

            png_url = documents[1]["uploadUrl"]
            png_upload = await client.put(
                png_url,
                content=png_data,
                headers={"Content-Type": "image/png"},
            )
            print(f"  ✓ PNG uploaded: {png_upload.status_code}")

            # STEP 6: Complete upload
            print("\n✔️ Step 6: Completing upload...")
            complete_resp = await client.post(
                f"{SHEERID_BASE_URL}/rest/v2/verification/"
                f"{verification_id}/step/completeDocUpload"
            )
            print(f"✅ Upload completed: {complete_resp.status_code}")

            print("\n🎉 Verification submitted successfully!")
            return {"success": True, "message": "Submitted successfully"}

        except httpx.TimeoutException:
            msg = "Request timeout - please try again"
            print("❌", msg)
            return {"success": False, "message": msg}
        except Exception as e:
            msg = f"Submission error: {e}"
            print("❌", msg)
            return {"success": False, "message": msg}


# =====================================================
# MAIN FLOW (MIRIP CONVERSATION HANDLER)
# =====================================================

async def main_flow():
    line()
    print("🎓 K12 Teacher Verification - CLI")
    line()
    print("Flow sama dengan bot Telegram, tapi lewat terminal.\n")

    user_id = 1
    user_data[user_id] = {}

    # 1. Minta SheerID URL
    while True:
        url = prompt(
            "Send your SheerID verification URL:\n"
            "  https://services.sheerid.com/verify/.../verificationId=...\n\n"
            "URL: "
        )

        match = re.search(
            r"verificationId=([a-f0-9]{24})", url, re.IGNORECASE
        )
        if not match:
            print(
                "❌ Invalid URL!\n"
                "Pastikan ada parameter: verificationId=...\n"
            )
            continue

        verification_id = match.group(1)
        user_data[user_id]["verification_id"] = verification_id
        print(f"\n✅ Verification ID: {verification_id}\n")
        break

    # 2. Minta nama lengkap
    while True:
        full_name = prompt(
            "What's your full name? (contoh: Elizabeth Bradly)\nName: "
        )
        parts = full_name.split()
        if len(parts) < 2:
            print(
                "❌ Please provide first name AND last name "
                "(contoh: John Smith)"
            )
            continue
        user_data[user_id]["first_name"] = parts[0]
        user_data[user_id]["last_name"] = " ".join(parts[1:])
        user_data[user_id]["full_name"] = full_name
        print(f"\n✅ Name: {full_name}\n")
        break

    # 3. Minta email
    while True:
        email = prompt("What's your school email address?\nEmail: ")
        if "@" not in email or "." not in email:
            print("❌ Invalid email format! Coba lagi.")
            continue
        user_data[user_id]["email"] = email
        print(f"\n✅ Email: {email}\n")
        break

    # 4. Minta nama sekolah
    while True:
        school_name = prompt(
            "What's your school name? (contoh: The Clinton School)\nSchool: "
        )
        if not school_name:
            print("❌ Nama sekolah tidak boleh kosong.")
            continue

        user_data[user_id]["school_name"] = school_name
        print(
            f"\n⚙️ Searching for schools matching: {school_name}\n"
            "Please wait...\n"
        )

        schools = await search_schools(school_name)
        if not schools:
            print(
                "\n❌ No schools found!\n"
                "Coba ganti / persingkat nama sekolah.\n"
            )
            continue

        # Tampilkan & pilih sekolah
        idx = display_schools_cli(schools, school_name, user_id)
        selected_school = user_data[user_id][f"school_{idx}"]
        break

    # 5. Konfirmasi sekolah dan generate dokumen
    school = selected_school
    s_name = school.get("name")
    s_type = school.get("type", "K12")
    s_id = school.get("id")

    line()
    print("✅ Selected School:")
    print(f"Name: {s_name}")
    print(f"Type: {s_type}")
    print(f"ID  : {s_id}")
    print("\n⚙️ Generating documents...\n")

    verification_id = user_data[user_id]["verification_id"]
    first_name = user_data[user_id]["first_name"]
    last_name = user_data[user_id]["last_name"]
    full_name = user_data[user_id]["full_name"]
    email = user_data[user_id]["email"]

    # Generate dokumen (sama dengan button_callback)
    id_card, faculty_id = generate_faculty_id(full_name, email, s_name)
    pay_stub = generate_pay_stub(full_name, email, s_name, faculty_id)
    letter = generate_employment_letter(full_name, email, s_name)

    print("✅ Documents generated successfully")
    print(f"Faculty ID: {faculty_id}")

    # Simpan dokumen ke file lokal (biar bisa dicek)
    os.makedirs("output_docs", exist_ok=True)
    id_path = os.path.join("output_docs", "faculty_id.jpg")
    pay_path = os.path.join("output_docs", "pay_stub.jpg")
    letter_path = os.path.join("output_docs", "employment_letter.jpg")

    id_card.save(id_path, format="JPEG", quality=95)
    pay_stub.save(pay_path, format="JPEG", quality=95)
    letter.save(letter_path, format="JPEG", quality=95)

    print("\n📁 Files saved to 'output_docs' directory:")
    print(f"  - {id_path}")
    print(f"  - {pay_path}")
    print(f"  - {letter_path}")

    # Konversi ke bytes (untuk upload)
    pdf_bytes = image_to_bytes(pay_stub).getvalue()
    png_bytes = image_to_bytes(id_card).getvalue()

    print("\n⚙️ Submitting to SheerID...\n")

    result = await submit_sheerid(
        verification_id,
        first_name,
        last_name,
        email,
        school,
        pdf_bytes,
        png_bytes,
    )

    line()
    if result.get("success"):
        print("✅ VERIFICATION SUCCESS!")
        print()
        print(f"👤 Name   : {full_name}")
        print(f"🏫 School : {s_name}")
        print(f"📧 Email  : {email}")
        print(f"🆔 Faculty ID : {faculty_id}")
        print(f"🔗 Status : SUCCESS")
        print("\nType 'python3 k12_cli.py' untuk mulai lagi.")
    else:
        print("❌ VERIFICATION FAILED")
        print(f"Error: {result.get('message')}")
        print("\nSilakan coba lagi atau hubungi support.")
    line()


# =====================================================
# ENTRY POINT
# =====================================================

def main():
    try:
        asyncio.run(main_flow())
    except KeyboardInterrupt:
        print("\nProcess cancelled by user.")
    except Exception as e:
        print(f"\nFatal error: {e}")


if __name__ == "__main__":
    main()
