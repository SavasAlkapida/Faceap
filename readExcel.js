const XLSX = require('xlsx');
const path = require('path');

// Excel dosyasının yolunu belirtin
const excelFilePath = path.resolve(__dirname, 'data.xlsx');

// Excel dosyasını okuma
const workbook = XLSX.readFile(excelFilePath);

// İlk sayfayı seçme
const sheetName = workbook.SheetNames[0];
const worksheet = workbook.Sheets[sheetName];

// Sayfayı JSON formatına dönüştürme
const data = XLSX.utils.sheet_to_json(worksheet);

console.log(data);
