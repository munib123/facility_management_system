import pandas as pd
import numpy as np
from datetime import datetime
import re


class DataCleaner:
    """Generic data cleaning class for CSV files"""
    
    def __init__(self, df, name="DataFrame"):
        self.df = df.copy()
        self.name = name
        self.cleaning_report = []
        
    def log(self, message):
        """Log cleaning actions"""
        print(f"[{self.name}] {message}")
        self.cleaning_report.append(message)
    
    def remove_duplicates(self, subset=None):
        """Remove duplicate rows"""
        initial_count = len(self.df)
        self.df.drop_duplicates(subset=subset, inplace=True)
        removed = initial_count - len(self.df)
        if removed > 0:
            self.log(f"Removed {removed} duplicate rows")
        return self
    
    def handle_missing_values(self, strategy='auto'):
        """
        Handle missing values with different strategies
        strategy: 'auto', 'drop', 'fill_mean', 'fill_median', 'fill_mode', 'fill_forward'
        """
        missing_count = self.df.isnull().sum().sum()
        if missing_count == 0:
            self.log("No missing values found")
            return self
        
        self.log(f"Found {missing_count} missing values")
        
        if strategy == 'auto':
            for col in self.df.columns:
                if self.df[col].isnull().sum() > 0:
                    if self.df[col].dtype in ['int64', 'float64']:
                        # Fill numeric columns with median
                        self.df[col].fillna(self.df[col].median(), inplace=True)
                        self.log(f"  - Filled {col} (numeric) with median")
                    else:
                        # Fill categorical columns with mode
                        mode_val = self.df[col].mode()
                        if len(mode_val) > 0:
                            self.df[col].fillna(mode_val[0], inplace=True)
                            self.log(f"  - Filled {col} (categorical) with mode")
        elif strategy == 'drop':
            self.df.dropna(inplace=True)
            self.log(f"Dropped rows with missing values")
        
        return self
    
    def standardize_text_columns(self):
        """Standardize text columns: trim whitespace, fix case inconsistencies"""
        for col in self.df.select_dtypes(include=['object']).columns:
            # Remove leading/trailing whitespace
            self.df[col] = self.df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
            
            # Check if column appears to be categorical (limited unique values)
            unique_ratio = self.df[col].nunique() / len(self.df)
            if unique_ratio < 0.5:  # If less than 50% unique values
                self.df[col] = self.df[col].apply(lambda x: x.title() if isinstance(x, str) else x)
                self.log(f"Standardized text in '{col}' column")
        
        return self
    
    def clean_numeric_columns(self):
        """Clean numeric columns: remove outliers, fix data types"""
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            # Remove negative values where they don't make sense (costs, times, IDs)
            if any(keyword in col.lower() for keyword in ['id', 'cost', 'time', 'hours', 'mins', 'size', 'floor']):
                negative_count = (self.df[col] < 0).sum()
                if negative_count > 0:
                    self.df = self.df[self.df[col] >= 0]
                    self.log(f"Removed {negative_count} rows with negative values in '{col}'")
            
            # Handle outliers using IQR method (optional, can be toggled)
            Q1 = self.df[col].quantile(0.25)
            Q3 = self.df[col].quantile(0.75)
            IQR = Q3 - Q1
            
            # Flag extreme outliers (beyond 3*IQR)
            lower_bound = Q1 - 3 * IQR
            upper_bound = Q3 + 3 * IQR
            outliers = ((self.df[col] < lower_bound) | (self.df[col] > upper_bound)).sum()
            
            if outliers > 0 and outliers < len(self.df) * 0.05:  # Only if < 5% of data
                self.log(f"Found {outliers} extreme outliers in '{col}' (not removed, flagged only)")
        
        return self
    
    def parse_dates(self, date_columns=None):
        """Parse and validate date columns"""
        if date_columns is None:
            # Auto-detect date columns
            date_columns = [col for col in self.df.columns if 'date' in col.lower()]
        
        for col in date_columns:
            if col in self.df.columns:
                try:
                    self.df[col] = pd.to_datetime(self.df[col], errors='coerce')
                    invalid_dates = self.df[col].isnull().sum()
                    if invalid_dates > 0:
                        self.log(f"Found {invalid_dates} invalid dates in '{col}'")
                    else:
                        self.log(f"Parsed '{col}' as datetime")
                except Exception as e:
                    self.log(f"Could not parse '{col}' as date: {str(e)}")
        
        return self
    
    def validate_ids(self, id_columns=None):
        """Validate ID columns are unique and properly formatted"""
        if id_columns is None:
            # Auto-detect ID columns
            id_columns = [col for col in self.df.columns if 'id' in col.lower() and 'assigned' not in col.lower()]
        
        for col in id_columns:
            if col in self.df.columns:
                # Check for duplicates in primary ID columns
                if col.endswith('_ID') or col == 'Ticket_ID' or col == 'Cleaner_ID':
                    duplicates = self.df[col].duplicated().sum()
                    if duplicates > 0:
                        self.log(f"WARNING: Found {duplicates} duplicate IDs in '{col}'")
                
                # Check for missing IDs
                missing = self.df[col].isnull().sum()
                if missing > 0:
                    self.log(f"WARNING: Found {missing} missing values in '{col}'")
        
        return self
    
    def standardize_categories(self, category_mapping=None):
        """Standardize categorical values"""
        if category_mapping:
            for col, mapping in category_mapping.items():
                if col in self.df.columns:
                    self.df[col] = self.df[col].replace(mapping)
                    self.log(f"Applied category mapping to '{col}'")
        
        return self
    
    def remove_extra_whitespace(self):
        """Remove extra whitespace from string columns"""
        for col in self.df.select_dtypes(include=['object']).columns:
            self.df[col] = self.df[col].apply(
                lambda x: re.sub(r'\s+', ' ', x) if isinstance(x, str) else x
            )
        
        return self
    
    def reset_index(self):
        """Reset the dataframe index"""
        self.df.reset_index(drop=True, inplace=True)
        return self
    
    def get_cleaned_data(self):
        """Return the cleaned dataframe"""
        return self.df
    
    def get_report(self):
        """Return cleaning report"""
        return self.cleaning_report
    
    def save_to_csv(self, output_path):
        """Save cleaned data to CSV"""
        self.df.to_csv(output_path, index=False)
        self.log(f"Saved cleaned data to {output_path}")
        return self


def clean_all_datasets():
    """Main function to clean all datasets"""
    
    print("=" * 80)
    print("DATA CLEANING PIPELINE")
    print("=" * 80)
    
    # Load datasets
    df_locations = pd.read_csv('locations.csv')
    df_financials = pd.read_csv('financials.csv')
    df_staff = pd.read_csv('staff.csv')
    df_tickets = pd.read_csv('tickets.csv')
    
    # Clean Locations
    print("\n### CLEANING LOCATIONS ###")
    locations_cleaner = DataCleaner(df_locations, "Locations")
    df_locations_clean = (locations_cleaner
                          .remove_duplicates()
                          .handle_missing_values(strategy='auto')
                          .standardize_text_columns()
                          .clean_numeric_columns()
                          .validate_ids(['Location_ID'])
                          .remove_extra_whitespace()
                          .reset_index()
                          .get_cleaned_data())
    
    # Clean Financials
    print("\n### CLEANING FINANCIALS ###")
    financials_cleaner = DataCleaner(df_financials, "Financials")
    df_financials_clean = (financials_cleaner
                           .remove_duplicates()
                           .parse_dates(['Date'])
                           .handle_missing_values(strategy='auto')
                           .clean_numeric_columns()
                           .validate_ids(['Location_ID'])
                           .remove_extra_whitespace()
                           .reset_index()
                           .get_cleaned_data())
    
    # Clean Staff
    print("\n### CLEANING STAFF ###")
    staff_cleaner = DataCleaner(df_staff, "Staff")
    df_staff_clean = (staff_cleaner
                      .remove_duplicates()
                      .handle_missing_values(strategy='auto')
                      .standardize_text_columns()
                      .clean_numeric_columns()
                      .validate_ids(['Cleaner_ID', 'Assigned_Location_ID'])
                      .remove_extra_whitespace()
                      .reset_index()
                      .get_cleaned_data())
    
    # Clean Tickets
    print("\n### CLEANING TICKETS ###")
    tickets_cleaner = DataCleaner(df_tickets, "Tickets")
    df_tickets_clean = (tickets_cleaner
                        .remove_duplicates()
                        .parse_dates(['Date_reported'])
                        .handle_missing_values(strategy='auto')
                        .standardize_text_columns()
                        .clean_numeric_columns()
                        .validate_ids(['Ticket_ID', 'Location_ID', 'Staff_assigned'])
                        .remove_extra_whitespace()
                        .reset_index()
                        .get_cleaned_data())
    
    # Save cleaned datasets
    print("\n### SAVING CLEANED DATA ###")
    df_locations_clean.to_csv('locations_cleaned.csv', index=False)
    print("✓ Saved: locations_cleaned.csv")
    
    df_financials_clean.to_csv('financials_cleaned.csv', index=False)
    print("✓ Saved: financials_cleaned.csv")
    
    df_staff_clean.to_csv('staff_cleaned.csv', index=False)
    print("✓ Saved: staff_cleaned.csv")
    
    df_tickets_clean.to_csv('tickets_cleaned.csv', index=False)
    print("✓ Saved: tickets_cleaned.csv")
    
    # Summary statistics
    print("\n" + "=" * 80)
    print("CLEANING SUMMARY")
    print("=" * 80)
    print(f"Locations: {len(df_locations)} → {len(df_locations_clean)} rows")
    print(f"Financials: {len(df_financials)} → {len(df_financials_clean)} rows")
    print(f"Staff: {len(df_staff)} → {len(df_staff_clean)} rows")
    print(f"Tickets: {len(df_tickets)} → {len(df_tickets_clean)} rows")
    print("=" * 80)
    
    return df_locations_clean, df_financials_clean, df_staff_clean, df_tickets_clean


if __name__ == "__main__":
    # Run the cleaning pipeline
    locations, financials, staff, tickets = clean_all_datasets()
    
    print("\n✅ Data cleaning completed successfully!")
