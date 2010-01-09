/* 
Copyright 2010 Hardcoded Software (http://www.hardcoded.net)

This software is licensed under the "HS" License as described in the "LICENSE" file, 
which should be included with this package. The terms are also available at 
http://www.hardcoded.net/licenses/hs_license
*/

#import <Cocoa/Cocoa.h>
#import "PyImportTable.h"
#import "PyImportWindow.h"
#import "MGEditableTable.h"
#import "MGTableView.h"

@interface MGImportTable : MGEditableTable {}
- (id)initWithImportWindow:(PyImportWindow *)aWindow view:(MGTableView *)aTableView;
- (PyImportTable *)py;
- (void)bindLockClick:(id)sender;
@end