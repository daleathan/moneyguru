# Created By: Virgil Dupras
# Created On: 2009-11-28
# Copyright 2011 Hardcoded Software (http://www.hardcoded.net)
# 
# This software is licensed under the "BSD" License as described in the "LICENSE" file, 
# which should be included with this package. The terms are also available at 
# http://www.hardcoded.net/licenses/bsd_license

from PyQt4.QtCore import Qt
from PyQt4.QtGui import (QDialog, QMessageBox, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QComboBox, QSpinBox, QCheckBox, QDialogButtonBox, QSizePolicy, QSpacerItem)

from hscommon.currency import Currency
from hscommon.trans import tr as trbase

tr = lambda s: trbase(s, "PreferencesPanel")

SUPPORTED_LANGUAGES = ['en', 'fr', 'de', 'it']
LANG2NAME = {
    'en': tr('English'),
    'fr': tr('French'),
    'de': tr('German'),
    'it': tr('Italian'),
}

class PreferencesPanel(QDialog):
    def __init__(self, parent, app):
        # The flags we pass are that so we don't get the "What's this" button in the title bar
        QDialog.__init__(self, parent, Qt.WindowTitleHint | Qt.WindowSystemMenuHint)
        self.app = app
        self._setupUi()
        
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
    
    def _setupUi(self):
        self.setWindowTitle(tr("Preferences"))
        self.resize(332, 253)
        self.verticalLayout = QVBoxLayout(self)
        self.formLayout = QFormLayout()
        self.firstWeekdayComboBox = QComboBox(self)
        weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        self.firstWeekdayComboBox.addItems([tr(weekday) for weekday in weekdays])
        sizePolicy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.firstWeekdayComboBox.sizePolicy().hasHeightForWidth())
        self.firstWeekdayComboBox.setSizePolicy(sizePolicy)
        self.formLayout.addRow(tr("First day of the week:"), self.firstWeekdayComboBox)
        self.aheadMonthsSpinBox = QSpinBox(self)
        sizePolicy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.aheadMonthsSpinBox.sizePolicy().hasHeightForWidth())
        self.aheadMonthsSpinBox.setSizePolicy(sizePolicy)
        self.aheadMonthsSpinBox.setMaximum(11)
        self.aheadMonthsSpinBox.setValue(2)
        self.formLayout.addRow(tr("Ahead months in Running Year:"), self.aheadMonthsSpinBox)
        self.yearStartComboBox = QComboBox(self)
        months = ["January", "February", "March", "April", "May", "June", "July", "August",
            "September", "October", "November", "December"]
        self.yearStartComboBox.addItems([tr(month) for month in months])
        sizePolicy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.yearStartComboBox.sizePolicy().hasHeightForWidth())
        self.yearStartComboBox.setSizePolicy(sizePolicy)
        self.formLayout.addRow(tr("Year starts in:"), self.yearStartComboBox)
        self.horizontalLayout = QHBoxLayout()
        self.autoSaveIntervalSpinBox = QSpinBox(self)
        sizePolicy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.autoSaveIntervalSpinBox.sizePolicy().hasHeightForWidth())
        self.autoSaveIntervalSpinBox.setSizePolicy(sizePolicy)
        self.horizontalLayout.addWidget(self.autoSaveIntervalSpinBox)
        self.label_5 = QLabel(tr("minute(s) (0 for none)"), self)
        self.horizontalLayout.addWidget(self.label_5)
        self.formLayout.addRow(tr("Auto-save interval:"), self.horizontalLayout)
        self.nativeCurrencyComboBox = QComboBox(self)
        availableCurrencies = ['{currency.code} - {currency.name}'.format(currency=currency) for currency in Currency.all]
        self.nativeCurrencyComboBox.addItems(availableCurrencies)
        sizePolicy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.nativeCurrencyComboBox.sizePolicy().hasHeightForWidth())
        self.nativeCurrencyComboBox.setSizePolicy(sizePolicy)
        self.nativeCurrencyComboBox.setEditable(True)
        self.formLayout.addRow(tr("Native Currency:"), self.nativeCurrencyComboBox)
        self.languageComboBox = QComboBox(self)
        for lang in SUPPORTED_LANGUAGES:
            self.languageComboBox.addItem(LANG2NAME[lang])
        sizePolicy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.languageComboBox.sizePolicy().hasHeightForWidth())
        self.languageComboBox.setSizePolicy(sizePolicy)
        self.formLayout.addRow(tr("Language:"), self.languageComboBox)
        self.verticalLayout.addLayout(self.formLayout)
        self.scopeDialogCheckBox = QCheckBox(tr("Show scope dialog when modifying a scheduled transaction"), self)
        self.verticalLayout.addWidget(self.scopeDialogCheckBox)
        self.autoDecimalPlaceCheckBox = QCheckBox(tr("Automatically place decimals when typing"), self)
        self.verticalLayout.addWidget(self.autoDecimalPlaceCheckBox)
        spacerItem = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.buttonBox = QDialogButtonBox(self)
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
        self.verticalLayout.addWidget(self.buttonBox)
    
    def load(self):
        appm = self.app.model
        self.firstWeekdayComboBox.setCurrentIndex(appm.first_weekday)
        self.aheadMonthsSpinBox.setValue(appm.ahead_months)
        self.yearStartComboBox.setCurrentIndex(appm.year_start_month - 1)
        self.autoSaveIntervalSpinBox.setValue(appm.autosave_interval)
        self.nativeCurrencyComboBox.setCurrentIndex(Currency.all.index(appm.default_currency))
        self.scopeDialogCheckBox.setChecked(self.app.prefs.showScheduleScopeDialog)
        self.autoDecimalPlaceCheckBox.setChecked(appm.auto_decimal_place)
        try:
            langindex = SUPPORTED_LANGUAGES.index(self.app.prefs.language)
        except ValueError:
            langindex = 0
        self.languageComboBox.setCurrentIndex(langindex)
    
    def save(self):
        appm = self.app.model
        appm.first_weekday = self.firstWeekdayComboBox.currentIndex()
        appm.ahead_months = self.aheadMonthsSpinBox.value()
        appm.year_start_month = self.yearStartComboBox.currentIndex() + 1
        appm.autosave_interval = self.autoSaveIntervalSpinBox.value()
        if self.nativeCurrencyComboBox.currentIndex() >= 0:
            appm.default_currency = Currency.all[self.nativeCurrencyComboBox.currentIndex()]
        self.app.prefs.showScheduleScopeDialog = self.scopeDialogCheckBox.isChecked()
        appm.auto_decimal_place = self.autoDecimalPlaceCheckBox.isChecked()
        lang = SUPPORTED_LANGUAGES[self.languageComboBox.currentIndex()]
        oldlang = self.app.prefs.language
        if oldlang not in SUPPORTED_LANGUAGES:
            oldlang = 'en'
        if lang != oldlang:
            QMessageBox.information(self, "", tr("moneyGuru has to restart for language changes to take effect"))
        self.app.prefs.language = lang
    

if __name__ == '__main__':
    import sys
    from PyQt4.QtGui import QApplication, QDialog
    app = QApplication([])
    dialog = QDialog(None)
    PreferencesPanel._setupUi(dialog)
    dialog.show()
    sys.exit(app.exec_())