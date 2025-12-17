from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
import random
import io

def get_fonts():
    """Load fonts dengan fallback"""
    try:
        return {
            'title': ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28),
            'heading': ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20),
            'normal': ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16),
            'small': ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14),
        }
    except:
        default = ImageFont.load_default()
        return {'title': default, 'heading': default, 'normal': default, 'small': default}

def generate_faculty_id(teacher_name, teacher_email, school_name):
    """Generate Faculty ID Card realistis"""
    width, height = 850, 540
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    fonts = get_fonts()

    # Border
    draw.rectangle([(5, 5), (width-5, height-5)], outline='#1e3a8a', width=3)

    # Header dengan logo placeholder
    draw.rectangle([(0, 0), (width, 120)], fill='#1e40af')
    draw.ellipse([(30, 30), (90, 90)], fill='white')  # Logo circle
    draw.text((60, 60), "LOGO", fill='#1e40af', font=fonts['small'], anchor='mm')

    draw.text((width//2, 40), school_name.upper(), fill='white', font=fonts['title'], anchor='mm')
    draw.text((width//2, 80), "FACULTY IDENTIFICATION CARD", fill='white', font=fonts['normal'], anchor='mm')

    # Photo section
    photo_x, photo_y = 40, 150
    draw.rectangle([(photo_x, photo_y), (photo_x+220, photo_y+280)], fill='#e5e7eb', outline='#374151', width=2)
    draw.text((photo_x+110, photo_y+140), "FACULTY\nPHOTO", fill='#6b7280', font=fonts['heading'], anchor='mm', align='center')

    # Info section
    info_x = 300
    y_start = 160

    # Name
    draw.text((info_x, y_start), "NAME:", fill='#374151', font=fonts['small'])
    draw.text((info_x, y_start+25), teacher_name, fill='black', font=fonts['heading'])

    # Email
    draw.text((info_x, y_start+70), "EMAIL:", fill='#374151', font=fonts['small'])
    draw.text((info_x, y_start+95), teacher_email, fill='black', font=fonts['normal'])

    # Faculty ID
    faculty_id = f"FAC-{random.randint(10000, 99999)}"
    draw.text((info_x, y_start+140), "FACULTY ID:", fill='#374151', font=fonts['small'])
    draw.text((info_x, y_start+165), faculty_id, fill='black', font=fonts['heading'])

    # Department
    departments = ['Mathematics', 'English', 'Science', 'History', 'Physical Education']
    dept = random.choice(departments)
    draw.text((info_x, y_start+210), "DEPARTMENT:", fill='#374151', font=fonts['small'])
    draw.text((info_x, y_start+235), dept, fill='black', font=fonts['normal'])

    # Expiry date
    expiry = (datetime.now() + timedelta(days=365)).strftime('%m/%Y')
    draw.text((info_x, y_start+270), f"EXPIRES: {expiry}", fill='#dc2626', font=fonts['normal'])

    # Barcode
    draw.rectangle([(40, 460), (810, 500)], fill='black')
    for i in range(0, 770, 15):
        if random.choice([True, False]):
            draw.rectangle([(40+i, 460), (40+i+7, 500)], fill='white')
    draw.text((425, 515), faculty_id, fill='#374151', font=fonts['small'], anchor='mm')

    return img, faculty_id

def generate_pay_stub(teacher_name, teacher_email, school_name, faculty_id):
    """Generate slip gaji realistis"""
    width, height = 850, 1100
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    fonts = get_fonts()

    # Header
    draw.rectangle([(0, 0), (width, 100)], fill='#1e40af')
    draw.text((width//2, 30), school_name.upper(), fill='white', font=fonts['title'], anchor='mm')
    draw.text((width//2, 65), "PAYROLL STATEMENT", fill='white', font=fonts['heading'], anchor='mm')

    # Date info
    pay_date = datetime.now().strftime('%B %d, %Y')
    pay_period_start = (datetime.now() - timedelta(days=15)).strftime('%m/%d/%Y')
    pay_period_end = datetime.now().strftime('%m/%d/%Y')

    y = 130
    draw.text((50, y), f"Pay Date: {pay_date}", fill='black', font=fonts['normal'])
    draw.text((50, y+30), f"Pay Period: {pay_period_start} - {pay_period_end}", fill='black', font=fonts['normal'])

    # Employee info
    y = 200
    draw.rectangle([(40, y), (810, y+150)], outline='#374151', width=2)
    draw.text((60, y+20), "EMPLOYEE INFORMATION", fill='#1e40af', font=fonts['heading'])

    draw.text((60, y+60), f"Name: {teacher_name}", fill='black', font=fonts['normal'])
    draw.text((60, y+85), f"Email: {teacher_email}", fill='black', font=fonts['normal'])
    draw.text((60, y+110), f"Employee ID: {faculty_id}", fill='black', font=fonts['normal'])

    # Earnings
    y = 380
    draw.rectangle([(40, y), (810, y+250)], outline='#374151', width=2)
    draw.text((60, y+20), "EARNINGS", fill='#1e40af', font=fonts['heading'])

    # Salary details
    base_salary = random.randint(3500, 5500)
    benefits = random.randint(200, 400)
    total_gross = base_salary + benefits

    earnings = [
        ("Base Salary", f"${base_salary:,.2f}"),
        ("Benefits", f"${benefits:,.2f}"),
        ("", ""),
        ("GROSS PAY", f"${total_gross:,.2f}")
    ]

    line_y = y + 60
    for desc, amount in earnings:
        if desc:
            draw.text((60, line_y), desc, fill='black', font=fonts['normal'])
            draw.text((750, line_y), amount, fill='black', font=fonts['normal'], anchor='rm')
        if desc == "GROSS PAY":
            draw.line([(60, line_y-10), (750, line_y-10)], fill='#374151', width=2)
        line_y += 35

    # Deductions
    y = 660
    draw.rectangle([(40, y), (810, y+220)], outline='#374151', width=2)
    draw.text((60, y+20), "DEDUCTIONS", fill='#1e40af', font=fonts['heading'])

    fed_tax = total_gross * 0.15
    state_tax = total_gross * 0.05
    retirement = total_gross * 0.06
    total_deduct = fed_tax + state_tax + retirement

    deductions = [
        ("Federal Tax", f"${fed_tax:,.2f}"),
        ("State Tax", f"${state_tax:,.2f}"),
        ("Retirement (403b)", f"${retirement:,.2f}"),
        ("", ""),
        ("TOTAL DEDUCTIONS", f"${total_deduct:,.2f}")
    ]

    line_y = y + 60
    for desc, amount in deductions:
        if desc:
            draw.text((60, line_y), desc, fill='black', font=fonts['normal'])
            draw.text((750, line_y), amount, fill='black', font=fonts['normal'], anchor='rm')
        if desc == "TOTAL DEDUCTIONS":
            draw.line([(60, line_y-10), (750, line_y-10)], fill='#374151', width=2)
        line_y += 35

    # Net pay
    net_pay = total_gross - total_deduct
    y = 910
    draw.rectangle([(40, y), (810, y+100)], fill='#16a34a')
    draw.text((width//2, y+30), "NET PAY", fill='white', font=fonts['title'], anchor='mm')
    draw.text((width//2, y+65), f"${net_pay:,.2f}", fill='white', font=fonts['title'], anchor='mm')

    # Footer
    draw.text((width//2, 1050), "This is an official payroll document", fill='#6b7280', font=fonts['small'], anchor='mm')

    return img

def generate_employment_letter(teacher_name, teacher_email, school_name):
    """Generate surat keterangan kerja"""
    width, height = 850, 1100
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    fonts = get_fonts()

    # Letterhead
    draw.rectangle([(0, 0), (width, 120)], fill='#1e40af')
    draw.text((width//2, 40), school_name.upper(), fill='white', font=fonts['title'], anchor='mm')
    draw.text((width//2, 75), "Office of Human Resources", fill='white', font=fonts['normal'], anchor='mm')

    # Date
    today = datetime.now().strftime('%B %d, %Y')
    draw.text((650, 160), today, fill='black', font=fonts['normal'])

    # Letter content
    y = 220
    draw.text((100, y), "TO WHOM IT MAY CONCERN", fill='black', font=fonts['heading'])

    hire_year = random.randint(2018, 2023)

    letter_text = [
        f"This letter is to certify that {teacher_name} is currently employed",
        f"as a full-time faculty member at {school_name}.",
        "",
        f"Employment Start Date: August {hire_year}",
        f"Position: Teacher",
        f"Status: Active - Full Time",
        f"Email: {teacher_email}",
        "",
        f"{teacher_name} is a valued member of our teaching staff and",
        "maintains good standing with the institution.",
        "",
        "This letter is issued for verification purposes.",
        "",
        "Should you require additional information, please contact our",
        "Human Resources Department.",
    ]

    line_y = y + 50
    for line in letter_text:
        draw.text((100, line_y), line, fill='black', font=fonts['normal'])
        line_y += 35

    # Signature
    y = 850
    draw.line([(100, y), (400, y)], fill='#374151', width=2)
    draw.text((100, y+10), "Dr. Sarah Johnson", fill='black', font=fonts['normal'])
    draw.text((100, y+35), "Director of Human Resources", fill='#6b7280', font=fonts['small'])
    draw.text((100, y+60), school_name, fill='#6b7280', font=fonts['small'])

    # Official stamp placeholder
    draw.ellipse([(550, 800), (750, 1000)], outline='#dc2626', width=3)
    draw.text((650, 900), "OFFICIAL\nSEAL", fill='#dc2626', font=fonts['heading'], anchor='mm', align='center')

    return img

def image_to_bytes(image):
    """Convert PIL Image ke bytes"""
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG', quality=95)
    img_byte_arr.seek(0)
    return img_byte_arr
