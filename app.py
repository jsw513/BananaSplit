#!/usr/bin/env python3
"""BananaSplit: local-first macOS folder planning studio."""
import json,sys,subprocess
from pathlib import Path
from PySide6.QtCore import Qt,QSettings,QTimer
from PySide6.QtGui import QFont,QKeySequence,QShortcut
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QPlainTextEdit,QFileDialog,QComboBox,QTableWidget,QTableWidgetItem,QMessageBox,QFrame,QCheckBox,QLineEdit,QTabWidget,QSplitter,QSpinBox,QAbstractItemView)
from engine import read_text,read_table,from_json,extract,dedupe,plan,create,undo,SUPPORTED,sequence,interpret_sequence,plan_paths,create_paths,valid_folder_path

DARK='''
QWidget {background:#101114;color:#F2F1ED;font-family:Arial;font-size:13px}
QMainWindow {background:#101114}
QFrame#card {background:#1A1C20;border:1px solid #32343B;border-radius:16px}
QLabel#title {font-size:30px;font-weight:800;color:#FFE07A}
QLabel#sub {color:#A7A8AE;font-size:12px}
QLabel#section {font-size:15px;font-weight:700}
QPushButton {background:#303238;border:1px solid #474950;border-radius:9px;padding:9px 13px;font-weight:600}
QPushButton:hover {background:#45474D}
QPushButton#primary {background:#FFD45A;color:#191815;border:0;font-weight:800;font-size:14px}
QPushButton#primary:hover {background:#FFE38A}
QPushButton#danger {background:#39262B;color:#FFC2CA}
QPushButton:disabled {background:#27282B;color:#777980}
QPlainTextEdit,QLineEdit,QComboBox,QSpinBox,QTableWidget {background:#16181C;border:1px solid #373A41;border-radius:9px;padding:7px;selection-background-color:#806321}
QTableWidget {gridline-color:#303238;alternate-background-color:#1C1E22}
QHeaderView::section {background:#25272B;color:#D8D8D5;padding:8px;border:0}
QTabWidget::pane {border:0}
QTabBar::tab {background:#222429;padding:11px 16px;margin-right:5px;border-radius:8px;color:#B9BAC0}
QTabBar::tab:selected {background:#5C4A20;color:#FFE18A}
QCheckBox {spacing:7px}
'''
LIGHT='''
QWidget {background:#F5F3EC;color:#242526;font-family:Arial;font-size:13px}
QFrame#card {background:#FFFFFF;border:1px solid #DEDED9;border-radius:16px}
QLabel#title {font-size:30px;font-weight:800;color:#8B6600}
QLabel#sub {color:#6B6E75;font-size:12px}
QLabel#section {font-size:15px;font-weight:700}
QPushButton {background:#EAE9E3;border:1px solid #D3D1C9;border-radius:9px;padding:9px 13px;font-weight:600}
QPushButton:hover {background:#DDDAD0}
QPushButton#primary {background:#E6B52C;color:#181715;border:0;font-weight:800;font-size:14px}
QPushButton#danger {background:#FCE4E4;color:#7D2828}
QPushButton:disabled {color:#999;background:#E7E7E4}
QPlainTextEdit,QLineEdit,QComboBox,QSpinBox,QTableWidget {background:#FFF;border:1px solid #D4D2CC;border-radius:9px;padding:7px;selection-background-color:#E6C15B}
QTableWidget {alternate-background-color:#F5F5F2}
QHeaderView::section {background:#E9E8E1;padding:8px;border:0}
QTabWidget::pane {border:0}
QTabBar::tab {background:#E4E3DD;padding:11px 16px;margin-right:5px;border-radius:8px}
QTabBar::tab:selected {background:#F1D477}
'''

class Window(QMainWindow):
    def __init__(self):
        super().__init__();self.settings=QSettings('BananaSplit','BananaSplit');self.source=None;self.tables={};self.names=[];self.review=[];self.excluded=[];self.last_created=[];self.sequence_names=[];self.destination=Path(self.settings.value('destination',str(Path.home())));self.setWindowTitle('BananaSplit · Folder Studio');self.resize(1120,790);self.setMinimumSize(880,630);self.setAcceptDrops(True)
        base=QWidget();self.setCentralWidget(base);main=QVBoxLayout(base);main.setContentsMargins(24,20,24,20);main.setSpacing(14)
        header=QHBoxLayout();brand=QVBoxLayout();title=QLabel('🍌  BananaSplit');title.setObjectName('title');brand.addWidget(title);tag=QLabel('The folder studio for messy lists and beautiful organization.');tag.setObjectName('sub');brand.addWidget(tag);header.addLayout(brand);header.addStretch();self.theme=QComboBox();self.theme.addItems(['Midnight Banana','Daylight']);self.theme.setCurrentText(self.settings.value('theme','Midnight Banana'));self.theme.currentTextChanged.connect(self.apply_theme);header.addWidget(self.theme);main.addLayout(header)
        split=QSplitter(Qt.Horizontal);main.addWidget(split,1)
        left=QWidget();ll=QVBoxLayout(left);ll.setContentsMargins(0,0,8,0);ll.setSpacing(12);split.addWidget(left)
        self.tabs=QTabWidget();ll.addWidget(self.tabs,1)
        paste_tab=QWidget();pv=QVBoxLayout(paste_tab);pv.addWidget(self.heading('Paste anything'));hint=QLabel('Copy from an email, text message, website or document.\nSmart mode suggests names and flags uncertain wording.');hint.setObjectName('sub');hint.setWordWrap(True);pv.addWidget(hint)
        self.paste=QPlainTextEdit();self.paste.setPlaceholderText('Hey! Please make folders for kitchen, living room, exterior shots and behind-the-scenes. Don\'t worry about the garage yet.');self.paste.textChanged.connect(self.refresh);pv.addWidget(self.paste,1);self.tabs.addTab(paste_tab,'✦ Paste & Interpret')
        file_tab=QWidget();fv=QVBoxLayout(file_tab);fv.addWidget(self.heading('Import a source'));fv.addWidget(QLabel('Drop a file anywhere in this window or choose one below.'));browse=QPushButton('＋  Choose file…');browse.clicked.connect(self.browse);fv.addWidget(browse);self.file_label=QLabel('TXT · RTF · Markdown · EML · CSV · TSV · XLSX · JSON');self.file_label.setWordWrap(True);self.file_label.setObjectName('sub');fv.addWidget(self.file_label)
        self.sheet=QComboBox();self.sheet.currentTextChanged.connect(self.change_sheet);fv.addWidget(QLabel('Worksheet / data table'));fv.addWidget(self.sheet)
        self.column=QComboBox();self.column.currentIndexChanged.connect(self.refresh);fv.addWidget(QLabel('Folder name column'));fv.addWidget(self.column)
        self.headercheck=QCheckBox('First row is a header');self.headercheck.setChecked(True);self.headercheck.toggled.connect(self.refresh);fv.addWidget(self.headercheck);self.nested_excel=QCheckBox('Build nested folders from all populated columns (left to right)');self.nested_excel.toggled.connect(self.refresh);fv.addWidget(self.nested_excel);fv.addStretch();self.tabs.addTab(file_tab,'↥ Import File')
        seq_tab=QWidget();sv=QVBoxLayout(seq_tab);sv.addWidget(self.heading('Sequence generator'))
        sh=QLabel('Type a request or build a numbered sequence with precise controls.');sh.setObjectName('sub');sh.setWordWrap(True);sv.addWidget(sh)
        self.sequence_request=QLineEdit();self.sequence_request.setPlaceholderText('Create shot-01 through shot-10');sv.addWidget(self.sequence_request)
        parse_seq=QPushButton('✦ Interpret sequence request');parse_seq.clicked.connect(self.parse_sequence_request);sv.addWidget(parse_seq)
        sr=QHBoxLayout();self.seq_prefix=QLineEdit('shot-');self.seq_prefix.setPlaceholderText('Prefix');self.seq_suffix=QLineEdit();self.seq_suffix.setPlaceholderText('Suffix');sr.addWidget(self.seq_prefix);sr.addWidget(self.seq_suffix);sv.addLayout(sr)
        sn=QHBoxLayout();self.seq_start=QSpinBox();self.seq_end=QSpinBox();self.seq_digits=QSpinBox();self.seq_step=QSpinBox()
        for w,lo,hi,val in ((self.seq_start,0,999999,1),(self.seq_end,0,999999,10),(self.seq_digits,1,8,2),(self.seq_step,1,9999,1)):
            w.setRange(lo,hi);w.setValue(val);sn.addWidget(w)
        sv.addWidget(QLabel('Start                       End                       Digits                       Step'));sv.addLayout(sn)
        self.seq_apply=QPushButton('Generate sequence preview');self.seq_apply.clicked.connect(self.generate_sequence);sv.addWidget(self.seq_apply);sv.addStretch()
        self.tabs.addTab(seq_tab,'# Sequences')
        self.tabs.currentChanged.connect(self.refresh)
        opts=QFrame();opts.setObjectName('card');ov=QVBoxLayout(opts);ov.addWidget(self.heading('Interpretation'))
        self.mode=QComboBox();self.mode.addItems(['Smart suggestions','Literal list']);self.mode.currentTextChanged.connect(self.refresh);ov.addWidget(self.mode)
        self.commas=QCheckBox('Split commas and list separators');self.commas.setChecked(True);self.commas.toggled.connect(self.refresh);ov.addWidget(self.commas)
        self.review_label=QLabel('');self.review_label.setObjectName('sub');self.review_label.setWordWrap(True);ov.addWidget(self.review_label);ll.addWidget(opts)
        right=QWidget();rl=QVBoxLayout(right);rl.setContentsMargins(8,0,0,0);rl.setSpacing(11);split.addWidget(right);split.setSizes([430,640])
        dest=QFrame();dest.setObjectName('card');dv=QVBoxLayout(dest);dv.addWidget(self.heading('01  Destination'));dr=QHBoxLayout();self.dest_label=QLabel(str(self.destination));self.dest_label.setWordWrap(True);self.dest_label.setObjectName('sub');dr.addWidget(self.dest_label,1);pick=QPushButton('Browse…');pick.clicked.connect(self.pick_destination);dr.addWidget(pick);dv.addLayout(dr);rl.addWidget(dest)
        names=QFrame();names.setObjectName('card');nv=QVBoxLayout(names);top=QHBoxLayout();self.preview_title=self.heading('02  Folder preview');top.addWidget(self.preview_title);top.addStretch();add=QPushButton('＋ Add');add.clicked.connect(self.add_name);top.addWidget(add);remove=QPushButton('− Remove');remove.clicked.connect(self.remove_selected);top.addWidget(remove);nv.addLayout(top)
        self.table=QTableWidget(0,2);self.table.setHorizontalHeaderLabels(['Folder name (double-click to edit)','Status']);self.table.horizontalHeader().setStretchLastSection(False);self.table.horizontalHeader().setSectionResizeMode(0,self.table.horizontalHeader().ResizeMode.Stretch);self.table.setColumnWidth(1,90);self.table.setSelectionBehavior(QAbstractItemView.SelectRows);self.table.setSelectionMode(QAbstractItemView.ExtendedSelection);self.table.setAlternatingRowColors(True);self.table.itemChanged.connect(self.table_edited);nv.addWidget(self.table,1);rl.addWidget(names,1)
        tools=QFrame();tools.setObjectName('card');tv=QVBoxLayout(tools);tv.addWidget(self.heading('03  Naming studio'));r1=QHBoxLayout();self.prefix=QLineEdit();self.prefix.setPlaceholderText('Prefix');self.suffix=QLineEdit();self.suffix.setPlaceholderText('Suffix');r1.addWidget(self.prefix);r1.addWidget(self.suffix);tv.addLayout(r1)
        r2=QHBoxLayout();self.number=QCheckBox('Number folders');r2.addWidget(self.number);self.start=QSpinBox();self.start.setRange(0,99999);self.start.setValue(1);r2.addWidget(self.start);self.casing=QComboBox();self.casing.addItems(['Original','Title Case','UPPERCASE','lowercase']);r2.addWidget(self.casing,1);tv.addLayout(r2)
        r3=QHBoxLayout();self.find=QLineEdit();self.find.setPlaceholderText('Find text');self.replace=QLineEdit();self.replace.setPlaceholderText('Replace with');r3.addWidget(self.find);r3.addWidget(self.replace);tv.addLayout(r3)
        for widget in (self.prefix,self.suffix,self.find,self.replace):widget.textChanged.connect(self.render)
        for widget in (self.number,self.start,self.casing):
            (widget.toggled if isinstance(widget,QCheckBox) else widget.valueChanged if isinstance(widget,QSpinBox) else widget.currentTextChanged).connect(self.render)
        rl.addWidget(tools)
        footer=QHBoxLayout();self.status=QLabel('Ready when you are.');self.status.setObjectName('sub');footer.addWidget(self.status,1);undo_btn=QPushButton('↶ Undo last batch');undo_btn.clicked.connect(self.undo_last);footer.addWidget(undo_btn);self.create_btn=QPushButton('🍌  Create folders');self.create_btn.setObjectName('primary');self.create_btn.clicked.connect(self.create_folders);footer.addWidget(self.create_btn);main.addLayout(footer)
        self.apply_theme();self.refresh();QShortcut(QKeySequence('Meta+O'),self,browse.click);QShortcut(QKeySequence('Meta+Return'),self,self.create_folders)
    def parse_sequence_request(self):
        try:
            found=interpret_sequence(self.sequence_request.text())
            if not found:raise ValueError('Try a range such as "shot-01 through shot-10". You can also use the controls below.')
            self.sequence_names=found;self.refresh()
        except ValueError as exc:QMessageBox.warning(self,'Sequence request',str(exc))
    def generate_sequence(self):
        try:
            self.sequence_names=sequence(self.seq_prefix.text(),self.seq_start.value(),self.seq_end.value(),self.seq_digits.value(),self.seq_suffix.text(),self.seq_step.value());self.refresh()
        except ValueError as exc:QMessageBox.warning(self,'Invalid sequence',str(exc))
    def heading(self,s):
        w=QLabel(s);w.setObjectName('section');return w
    def apply_theme(self,*_):
        self.setStyleSheet(DARK if self.theme.currentIndex()==0 else LIGHT);self.settings.setValue('theme',self.theme.currentText())
    def browse(self):
        path,_=QFileDialog.getOpenFileName(self,'Choose information source',str(Path.home()),'Supported (*.txt *.rtf *.md *.eml *.csv *.tsv *.xlsx *.xlsm *.json);;All files (*)')
        if path:self.load_file(Path(path))
    def load_file(self,path):
        try:
            if path.suffix.lower() not in SUPPORTED:raise ValueError('Unsupported file format')
            self.source=path;self.tables={}
            if path.suffix.lower() in ('.csv','.tsv','.xlsx','.xlsm'):
                self.tables=read_table(path);self.sheet.blockSignals(True);self.sheet.clear();self.sheet.addItems(self.tables.keys());self.sheet.blockSignals(False);self.change_sheet()
            elif path.suffix.lower()=='.json':
                self.names=dedupe(from_json(path));self.review=[];self.excluded=[]
            else:
                self.file_text=read_text(path)
            self.file_label.setText('Loaded: '+path.name);self.tabs.setCurrentIndex(1);self.refresh()
        except Exception as exc:QMessageBox.critical(self,'Could not import',str(exc))
    def change_sheet(self,*_):
        rows=self.tables.get(self.sheet.currentText(),[]);self.column.blockSignals(True);self.column.clear()
        for i in range(max((len(row) for row in rows),default=0)):
            n=i+1;letter=''
            while n:n,r=divmod(n-1,26);letter=chr(65+r)+letter
            header=str(rows[0][i])[:30] if rows and i<len(rows[0]) and rows[0][i] is not None else ''
            self.column.addItem(f'{letter}  {header}',i)
        self.column.blockSignals(False);self.refresh()
    def refresh(self,*_):
        if self.tabs.currentIndex()==2:
            self.names=list(self.sequence_names);self.review=[];self.excluded=[]
        elif self.tabs.currentIndex()==0:
            text=self.paste.toPlainText();self.names,self.review,self.excluded=extract(text,'literal' if self.mode.currentIndex()==1 else 'smart',self.commas.isChecked())
        elif self.source:
            if self.tables:
                rows=self.tables.get(self.sheet.currentText(),[]);col=self.column.currentData();self.names=(dedupe(['/'.join(str(v).strip() for v in row if v is not None and str(v).strip()) for row in rows[int(self.headercheck.isChecked()):]]) if self.nested_excel.isChecked() else dedupe([str(row[col]) for row in rows[int(self.headercheck.isChecked()):] if col is not None and len(row)>col and row[col] is not None]));self.review=[];self.excluded=[]
            elif self.source.suffix.lower()=='.json':self.names=dedupe(from_json(self.source));self.review=[];self.excluded=[]
            else:self.names,self.review,self.excluded=extract(self.file_text,'literal' if self.mode.currentIndex()==1 else 'smart',self.commas.isChecked())
        else:self.names=[];self.review=[];self.excluded=[]
        self.review_label.setText(f'Needs review: {len(self.review)}  ·  Excluded: {len(self.excluded)}' + ('\nReview skipped text before creating.' if self.review else ''))
        self.render()
    def planned(self):
        # Transform leaf names, preserving hierarchy in path mode.
        paths=[]
        for index,original in enumerate(self.names):
            parts=str(original).split('/')
            leaf=parts[-1]
            if self.find.text():leaf=leaf.replace(self.find.text(),self.replace.text())
            if self.casing.currentText()=='Title Case':leaf=leaf.title()
            elif self.casing.currentText()=='UPPERCASE':leaf=leaf.upper()
            elif self.casing.currentText()=='lowercase':leaf=leaf.lower()
            leaf=self.prefix.text()+leaf+self.suffix.text()
            if self.number.isChecked():leaf=f'{self.start.value()+index:02d} - {leaf}'
            parts[-1]=leaf;paths.append('/'.join(parts))
        return plan_paths(paths,self.destination)
    def render(self,*_):
        rows=self.planned();self.table.blockSignals(True);self.table.setRowCount(len(rows))
        for i,(name,status) in enumerate(rows):
            self.table.setItem(i,0,QTableWidgetItem(name));st=QTableWidgetItem(status);st.setFlags(st.flags() & ~Qt.ItemIsEditable);self.table.setItem(i,1,st)
        self.table.blockSignals(False);self.preview_title.setText(f'02  Folder preview · {len(rows)}');self.create_btn.setEnabled(any(s=='Ready' for _,s in rows));self.status.setText(f'{sum(s=="Ready" for _,s in rows)} ready · {sum(s=="Exists" for _,s in rows)} already exist')
    def table_edited(self,item):
        if item.column()!=0:return
        # Direct edits become the new names; disable transformations to avoid double application.
        rows=[self.table.item(i,0).text() for i in range(self.table.rowCount())];self.names=dedupe(rows)
        for w in (self.prefix,self.suffix,self.find,self.replace):w.blockSignals(True);w.clear();w.blockSignals(False)
        self.number.blockSignals(True);self.number.setChecked(False);self.number.blockSignals(False)
        self.casing.blockSignals(True);self.casing.setCurrentIndex(0);self.casing.blockSignals(False);self.render()
    def add_name(self):
        from PySide6.QtWidgets import QInputDialog
        name,ok=QInputDialog.getText(self,'Add folder','Folder name:')
        if ok:self.names=dedupe(self.names+[name]);self.render()
    def remove_selected(self):
        selected={i.row() for i in self.table.selectedIndexes()};current=[self.table.item(i,0).text() for i in range(self.table.rowCount()) if i not in selected];self.names=dedupe(current)
        for w in (self.prefix,self.suffix,self.find,self.replace):w.blockSignals(True);w.clear();w.blockSignals(False)
        self.number.blockSignals(True);self.number.setChecked(False);self.number.blockSignals(False);self.casing.blockSignals(True);self.casing.setCurrentIndex(0);self.casing.blockSignals(False);self.render()
    def pick_destination(self):
        path=QFileDialog.getExistingDirectory(self,'Choose destination',str(self.destination))
        if path:self.destination=Path(path);self.settings.setValue('destination',path);self.dest_label.setText(path);self.render()
    def create_folders(self):
        rows=self.planned();ready=[n for n,s in rows if s=='Ready']
        if not ready:return
        if QMessageBox.question(self,'Confirm folder creation',f'Create {len(ready)} folders inside:\n{self.destination}\n\nNothing existing will be overwritten.',QMessageBox.Yes|QMessageBox.Cancel,QMessageBox.Yes)!=QMessageBox.Yes:return
        try:made,skipped,errors=create_paths([n for n,_ in rows],self.destination)
        except Exception as exc:QMessageBox.critical(self,'Creation failed',str(exc));return
        self.last_created=made;self.render();self.status.setText(f'🍌 Created {len(made)} folders · {len(skipped)} skipped · {len(errors)} errors')
        msg=f'Created {len(made)} folders. Skipped {len(skipped)} existing.'
        if errors:msg+='\n\nErrors:\n'+'\n'.join(errors[:12])
        QMessageBox.information(self,'BananaSplit complete',msg)
    def undo_last(self):
        if not self.last_created:QMessageBox.information(self,'Nothing to undo','No folders were created in this session.');return
        if QMessageBox.question(self,'Undo last batch','Remove folders from the last batch? Only empty folders will be removed.',QMessageBox.Yes|QMessageBox.Cancel,QMessageBox.Cancel)!=QMessageBox.Yes:return
        removed,failed=undo(self.last_created);self.last_created=[p for p in self.last_created if p not in removed];self.render();QMessageBox.information(self,'Undo result',f'Removed {len(removed)} empty folders. Could not remove {len(failed)} (possibly not empty).')
    def dragEnterEvent(self,event):
        if event.mimeData().hasUrls() and any(Path(u.toLocalFile()).suffix.lower() in SUPPORTED for u in event.mimeData().urls() if u.isLocalFile()):event.acceptProposedAction()
    def dropEvent(self,event):
        for u in event.mimeData().urls():
            p=Path(u.toLocalFile())
            if p.is_file() and p.suffix.lower() in SUPPORTED:self.load_file(p);event.acceptProposedAction();break

class App(QApplication):
    def event(self,event):
        if event.type()==event.Type.FileOpen and getattr(self,'window',None):
            p=event.file()
            if p:QTimer.singleShot(0,lambda:self.window.load_file(Path(p)))
            return True
        return super().event(event)

if __name__=='__main__':
    app=App(sys.argv);app.setApplicationName('BananaSplit');win=Window();app.window=win;win.show()
    if len(sys.argv)>1 and Path(sys.argv[1]).is_file():QTimer.singleShot(0,lambda:win.load_file(Path(sys.argv[1])))
    sys.exit(app.exec())
