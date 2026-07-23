const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const path = require('path');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const db = require('./database'); 
const ExcelJS = require('exceljs');
const PDFDocument = require('pdfkit');
const { Document, Packer, Table, TableRow, TableCell, Paragraph } = require('docx');

const app = express(); 
const PORT = 4000;
const JWT_SECRET = 'fuel_tracker_2024';

app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'public')));

// ============ AUTH MIDDLEWARE ============
const authenticateToken = (req, res, next) => {
  const token = req.headers['authorization']?.split(' ')[1];
  if (!token) return res.status(401).json({ error: 'No token' });
  
  jwt.verify(token, JWT_SECRET, (err, user) => {
    if (err) return res.status(403).json({ error: 'Invalid token' });
    req.user = user;
    next();
  });
};

// ============ LOGIN ============
app.post('/api/login', (req, res) => {
  const { username, password } = req.body;
  
  db.get('SELECT * FROM users WHERE username = ?', [username], (err, user) => {
    if (!user) return res.status(401).json({ error: 'Invalid credentials' });
    
    bcrypt.compare(password, user.password, (err, isMatch) => {
      if (!isMatch) return res.status(401).json({ error: 'Invalid credentials' });
      
      const token = jwt.sign(
        { id: user.id, username: user.username, role: user.role },
        JWT_SECRET
      );
      
      res.json({
        token,
        user: { id: user.id, username: user.username, role: user.role }
      });
    });
  });
});

// ============ CHECK SETUP - CREATE ADMIN ============
app.get('/api/check-setup', (req, res) => {
  db.get('SELECT COUNT(*) as count FROM users', (err, row) => {
    if (row.count === 0) {
      const hashedPassword = bcrypt.hashSync('admin123', 10);
      db.run(
        'INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
        ['headadmin', hashedPassword, 'Head Admin'],
        () => {
          res.json({ setup: true, message: 'Admin created: headadmin / admin123' });
        }
      );
    } else {
      res.json({ setup: false });
    }
  });
});

// ============ FUEL ENTRY - FIXED STOCK LOGIC ============
app.post('/api/fuel-entry', authenticateToken, (req, res) => {
  const d = req.body;
  
  // Get last closing stock for this fuel type
  db.get(
    'SELECT closing_stock FROM fuel_entries WHERE fuel_type = ? ORDER BY date DESC LIMIT 1',
    [d.fuel_type],
    (err, last) => {
      let opening = 0;
      
      // FIXED: Use last closing stock OR initial stock from form
      if (last && last.closing_stock) {
        opening = last.closing_stock;
      } else if (d.opening_stock) {
        opening = parseFloat(d.opening_stock) || 0;
      }
      
      let purchase_qty = null;
      let issue_qty = null;
      let closing = opening;
      
      // Calculate closing stock based on transaction type
      if (d.transaction_type === 'Purchase') {
        purchase_qty = parseFloat(d.quantity) || 0;
        closing = opening + purchase_qty;
      } else {
        issue_qty = parseFloat(d.issue_quantity) || 0;
        closing = opening - issue_qty;
      }
      
      const variance = closing - (parseFloat(d.physical_stock) || 0);
      
      const query = `
        INSERT INTO fuel_entries (
          slip_no, transaction_type, fuel_type, date, quantity, rate, amount,
          vendor_name, vendor_location, vehicle_no, vin_no, registration_no,
          model_no, allocated_to, opening_odometer, closing_odometer, km_run,
          issue_quantity, mileage, opening_stock, purchase_qty, issue_qty,
          closing_stock, physical_stock, variance, recipient_name, receiver_name,
          approved_by, recorded_by, remarks
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `;
      
      const values = [
        d.slip_no, d.transaction_type, d.fuel_type, d.date,
        d.quantity || null, d.rate || null, d.amount || null,
        d.vendor_name || null, d.vendor_location || null,
        d.vehicle_no || null, d.vin_no || null, d.registration_no || null,
        d.model_no || null, d.allocated_to || null,
        d.opening_odometer || null, d.closing_odometer || null, d.km_run || null,
        d.issue_quantity || null, d.mileage || null,
        opening, purchase_qty, issue_qty, closing, d.physical_stock || null, variance,
        d.recipient_name || null, d.receiver_name || null,
        d.approved_by || null, req.user.username, d.remarks || null
      ];
      
      db.run(query, values, (err) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json({ success: true });
      });
    }
  );
});

// ============ GET ENTRIES ============
app.get('/api/fuel-entries', authenticateToken, (req, res) => {
  let query = 'SELECT * FROM fuel_entries WHERE 1=1';
  let params = [];
  
  if (req.query.fuel_type) {
    query += ' AND fuel_type = ?';
    params.push(req.query.fuel_type);
  }
  if (req.query.transaction_type) {
    query += ' AND transaction_type = ?';
    params.push(req.query.transaction_type);
  }
  if (req.query.date_from && req.query.date_to) {
    query += ' AND date BETWEEN ? AND ?';
    params.push(req.query.date_from, req.query.date_to);
  }
  if (req.query.search) {
    query += ' AND (slip_no LIKE ? OR vehicle_no LIKE ? OR fuel_type LIKE ? OR allocated_to LIKE ? OR approved_by LIKE ?)';
    params.push(
      `%${req.query.search}%`,
      `%${req.query.search}%`,
      `%${req.query.search}%`,
      `%${req.query.search}%`,
      `%${req.query.search}%`
    );
  }
  
  query += ' ORDER BY date DESC';
  
  db.all(query, params, (err, rows) => {
    res.json(rows || []);
  });
});

// ============ DELETE ENTRY ============
app.delete('/api/fuel-entry/:id', authenticateToken, (req, res) => {
  db.run('DELETE FROM fuel_entries WHERE id = ?', [req.params.id], () => {
    res.json({ success: true });
  });
});

// ============ DASHBOARD - FIXED OLD STOCK ============
app.get('/api/dashboard', authenticateToken, (req, res) => {
  db.all('SELECT * FROM fuel_entries ORDER BY date ASC', (err, entries) => {
    const stats = {};
    
    entries.forEach(e => {
      if (!stats[e.fuel_type]) {
        stats[e.fuel_type] = {
          fuel_type: e.fuel_type,
          old_stock: 0,
          total_purchases: 0,
          total_allocated: 0,
          closing_stock: 0
        };
      }
      
      // Set old stock from FIRST entry with opening_stock (NOT mixed with purchases)
      if (stats[e.fuel_type].old_stock === 0 && e.opening_stock > 0) {
        stats[e.fuel_type].old_stock = e.opening_stock;
      }
      
      // Sum ONLY Purchase transactions
      if (e.transaction_type === 'Purchase') {
        stats[e.fuel_type].total_purchases += e.quantity || 0;
      }
      
      // Sum ONLY Issue transactions
      if (e.transaction_type === 'Issue') {
        stats[e.fuel_type].total_allocated += e.issue_quantity || 0;
      }
      
      // Always update closing stock to last entry
      stats[e.fuel_type].closing_stock = e.closing_stock || 0;
    });
    
    res.json({ stats: Object.values(stats) });
  });
});

// ============ EXPORT EXCEL ============
app.get('/api/export/excel', authenticateToken, (req, res) => {
  db.all('SELECT * FROM fuel_entries ORDER BY date DESC', async (err, entries) => {
    const workbook = new ExcelJS.Workbook();
    const worksheet = workbook.addWorksheet('Fuel Report');
    
    worksheet.addRow([
      'Date', 'Slip No', 'Type', 'Fuel Type', 'Vehicle No', 'VIN', 'Reg No', 'Model',
      'Allocated To', 'Opening Odo', 'Closing Odo', 'KM', 'Qty', 'Rate', 'Amount',
      'Mileage', 'Opening Stock', 'Closing Stock', 'Approved By', 'Remarks'
    ]);
    
    entries.forEach(e => {
      worksheet.addRow([
        e.date, e.slip_no, e.transaction_type, e.fuel_type, e.vehicle_no || '-',
        e.vin_no || '-', e.registration_no || '-', e.model_no || '-',
        e.allocated_to || '-', e.opening_odometer || '-', e.closing_odometer || '-',
        e.km_run || '-', e.quantity || e.issue_quantity || 0,
        e.rate || '-', e.amount || '-', e.mileage || '-',
        e.opening_stock || '-', e.closing_stock || '-', e.approved_by || '-', e.remarks || '-'
      ]);
    });
    
    res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
    res.setHeader('Content-Disposition', 'attachment; filename="Fuel_Report.xlsx"');
    await workbook.xlsx.write(res);
  });
});

// ============ EXPORT PDF ============
app.get('/api/export/pdf', authenticateToken, (req, res) => {
  db.all('SELECT * FROM fuel_entries ORDER BY date DESC', (err, entries) => {
    const doc = new PDFDocument();
    
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', 'attachment; filename="Fuel_Report.pdf"');
    doc.pipe(res);
    
    doc.fontSize(16).text('Fuel Tracking Report', 50, 50);
    doc.fontSize(10).text(`Generated: ${new Date().toLocaleString()}`, 50, 80);
    
    let y = 120;
    entries.slice(0, 100).forEach(e => {
      if (y > 700) {
        doc.addPage();
        y = 50;
      }
      doc.fontSize(9).text(
        `${e.date} | ${e.slip_no} | ${e.transaction_type} | ${e.fuel_type} | ${e.vehicle_no || '-'} | ${e.quantity || e.issue_quantity || 0}L`,
        50, y
      );
      y += 20;
    });
    
    doc.end();
  });
});

// ============ EXPORT WORD ============
app.get('/api/export/word', authenticateToken, (req, res) => {
  db.all('SELECT * FROM fuel_entries ORDER BY date DESC', async (err, entries) => {
    const rows = entries.slice(0, 50).map(e => new TableRow({
      children: [
        new TableCell({ children: [new Paragraph(e.date || '-')] }),
        new TableCell({ children: [new Paragraph(e.slip_no || '-')] }),
        new TableCell({ children: [new Paragraph(e.transaction_type || '-')] }),
        new TableCell({ children: [new Paragraph(e.fuel_type || '-')] }),
        new TableCell({ children: [new Paragraph(e.vehicle_no || '-')] }),
        new TableCell({ children: [new Paragraph(String(e.quantity || e.issue_quantity || 0))] })
      ]
    }));
    
    const doc = new Document({
      sections: [{
        children: [
          new Paragraph({ text: 'Fuel Tracking Report', style: 'Heading1' }),
          new Table({ rows })
        ]
      }]
    });
    
    const buffer = await Packer.toBuffer(doc);
    
    res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document');
    res.setHeader('Content-Disposition', 'attachment; filename="Fuel_Report.docx"');
    res.send(buffer);
  });
});

// ============ USERS ============
app.get('/api/users', authenticateToken, (req, res) => {
  db.all('SELECT id, username, role, created_at FROM users', (err, rows) => {
    res.json(rows || []);
  });
});

app.post('/api/users', authenticateToken, (req, res) => {
  const { username, password, role } = req.body;
  const hashedPassword = bcrypt.hashSync(password, 10);
  
  db.run(
    'INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
    [username, hashedPassword, role || 'User'],
    (err) => {
      if (err) return res.status(500).json({ error: err.message });
      res.json({ success: true });
    }
  );
});

app.delete('/api/users/:id', authenticateToken, (req, res) => {
  db.run('DELETE FROM users WHERE id = ?', [req.params.id], () => {
    res.json({ success: true });
  });
});

// ============ CHANGE PASSWORD ============
app.post('/api/change-password', authenticateToken, (req, res) => {
  const { oldPassword, newPassword } = req.body;
  
  db.get('SELECT password FROM users WHERE id = ?', [req.user.id], (err, user) => {
    bcrypt.compare(oldPassword, user.password, (err, isMatch) => {
      if (!isMatch) return res.status(401).json({ error: 'Wrong password' });
      
      const hashedPassword = bcrypt.hashSync(newPassword, 10);
      
      db.run(
        'UPDATE users SET password = ? WHERE id = ?',
        [hashedPassword, req.user.id],
        () => {
          res.json({ success: true });
        }
      );
    });
  });
});

// ============ START SERVER ============
app.listen(PORT, () => {
  console.log(` Server running at http://localhost:${PORT}`);
  console.log(` Setup: http://localhost:${PORT}/api/check-setup`);
  console.log(` Login: http://localhost:${PORT}`);
});
