import os

file_path = 'C:\\Users\\31621\\Desktop\\P21-DjangoTweet-main\\media\\merinos 492845 19-04-2024.pdf'
if os.path.exists(file_path):
    print(f'Dosya bulundu: {file_path}')
else:
    print(f'Dosya bulunamadı: {file_path}')
