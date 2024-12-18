from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
import smtplib

def send_mail(run, excel_files):
    try:
        subject = f'UDMMP | {run} Mane Clinical and genes incorrectly annotated FHL2, PDLIM3, ALKP3 and EYA4'
        email_sender = "udmmp.girona.ics@gencat.cat"
        image_path = '/home/udmmp/NGS_APP/AutoLauncherNGS/logo.png'

        # Crear el mensaje multipart
        msg = MIMEMultipart()
        msg['From'] = email_sender
        msg['Subject'] = subject
        emails = ['ocanal@idibgi.org']
        msg["To"] = ', '.join(emails)

        # Adjuntar el contenido del mensaje en formato HTML
        html = f"""
            <html>
                <body>
                    <p>=-=-=- No respongueu a aquest missatge, és un correu només d'informació =-=-=-=</p>

                    <p>Benvolgut/da,</p>

                    <p>L'informem de que el run {run} s'han analitzat les variants trobades en isoformes MANE Clinical i les trobades en els següents gens: ALKP3,FHL2, PDLIM3 i EYA4.:</p>

                    <p>Moltes gràcies.</p>

                    <div style="text-align: left;">
                        <img src="cid:image1" style="width:250px; height:auto; display:block; margin:0;">
                    </div>

                    <p>--</p>
                    <p>UDMMP | Unitat de Diagnóstic Molecular i Medicina Personalitzada<br>
                    Institut Català de la Salut | Generalitat de Catalunya<br>
                    Hospital Santa Caterina. Parc Hospitalari Martí i Julià<br>
                    C/Dr. Castany s/n | 17190 Salt | Tel. 972189023 | Ext. 9929</p>
                </body>
            </html>
        """
        msg.attach(MIMEText(html, 'html'))

        # Adjuntar la imagen
        with open(image_path, 'rb') as img:
            mime_image = MIMEImage(img.read())
            mime_image.add_header('Content-ID', '<image1>')
            mime_image.add_header('Content-Disposition', 'inline', filename='logo.png')
            msg.attach(mime_image)

        # Adjuntar los archivos Excel
        for file_path in excel_files:
            with open(file_path, 'rb') as excel_file:
                mime_excel = MIMEApplication(excel_file.read(), _subtype='vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                mime_excel.add_header('Content-Disposition', f'attachment; filename="{file_path.split("/")[-1]}"')
                msg.attach(mime_excel)

        # Enviar el correo
        with smtplib.SMTP("172.16.2.137", 25) as smtp:
            smtp.send_message(msg)

    except Exception as e:
        print(f"Error sending email: {e}")
        return
