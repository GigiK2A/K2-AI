import { StyleSheet, Font } from '@react-pdf/renderer'

// Registra font Inter
Font.register({
  family: 'Inter',
  fonts: [
    { src: 'https://fonts.gstatic.com/s/inter/v13/UcCO3FwrK3iLTeHuS_fvQtMwCp50KnMw2boKoduKmMEVuLyfAZ9hiA.woff2', fontWeight: 400 },
    { src: 'https://fonts.gstatic.com/s/inter/v13/UcCO3FwrK3iLTeHuS_fvQtMwCp50KnMw2boKoduKmMEVuGKYAZ9hiA.woff2', fontWeight: 600 },
    { src: 'https://fonts.gstatic.com/s/inter/v13/UcCO3FwrK3iLTeHuS_fvQtMwCp50KnMw2boKoduKmMEVuFuYAZ9hiA.woff2', fontWeight: 700 },
  ],
})

export const COLORS = {
  primary: '#1A1F36',
  accent: '#3B5BDB',
  green: '#2F9E44',
  orange: '#E67700',
  red: '#C92A2A',
  gray100: '#F8F9FA',
  gray300: '#DEE2E6',
  gray600: '#868E96',
  white: '#FFFFFF',
}

export const styles = StyleSheet.create({
  page: {
    fontFamily: 'Inter',
    fontSize: 10,
    color: '#212529',
    paddingTop: 48,
    paddingBottom: 56,
    paddingHorizontal: 48,
    backgroundColor: COLORS.white,
  },
  // Cover
  coverPage: {
    backgroundColor: COLORS.primary,
    padding: 56,
    justifyContent: 'space-between',
  },
  coverBadge: {
    backgroundColor: COLORS.accent,
    color: COLORS.white,
    fontSize: 9,
    fontWeight: 600,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 4,
    alignSelf: 'flex-start',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  coverTitle: {
    color: COLORS.white,
    fontSize: 28,
    fontWeight: 700,
    marginTop: 24,
    lineHeight: 1.3,
  },
  coverSubtitle: {
    color: '#A5B4FC',
    fontSize: 13,
    marginTop: 12,
  },
  coverMeta: {
    color: COLORS.gray600,
    fontSize: 9,
    marginTop: 48,
  },
  // Sezioni
  sectionTitle: {
    fontSize: 14,
    fontWeight: 700,
    color: COLORS.primary,
    marginBottom: 12,
    paddingBottom: 6,
    borderBottomWidth: 2,
    borderBottomColor: COLORS.accent,
  },
  subsectionTitle: {
    fontSize: 11,
    fontWeight: 600,
    color: COLORS.primary,
    marginTop: 14,
    marginBottom: 6,
  },
  bodyText: {
    fontSize: 10,
    lineHeight: 1.6,
    color: '#343A40',
  },
  // Tabelle
  table: { width: '100%', marginVertical: 10 },
  tableHeader: {
    flexDirection: 'row',
    backgroundColor: COLORS.primary,
    paddingVertical: 6,
    paddingHorizontal: 8,
  },
  tableHeaderCell: {
    color: COLORS.white,
    fontSize: 9,
    fontWeight: 600,
    flex: 1,
  },
  tableRow: {
    flexDirection: 'row',
    paddingVertical: 5,
    paddingHorizontal: 8,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.gray300,
  },
  tableRowAlt: {
    backgroundColor: COLORS.gray100,
  },
  tableCell: {
    fontSize: 9,
    color: '#343A40',
    flex: 1,
  },
  // Card automazione
  automationCard: {
    borderWidth: 1,
    borderColor: COLORS.gray300,
    borderRadius: 6,
    padding: 12,
    marginBottom: 8,
  },
  automationCardTitle: {
    fontSize: 11,
    fontWeight: 600,
    color: COLORS.primary,
    marginBottom: 4,
  },
  badge: {
    fontSize: 8,
    fontWeight: 600,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 3,
    alignSelf: 'flex-start',
    marginBottom: 6,
  },
  // Footer pagina
  pageFooter: {
    position: 'absolute',
    bottom: 24,
    left: 48,
    right: 48,
    flexDirection: 'row',
    justifyContent: 'space-between',
    borderTopWidth: 1,
    borderTopColor: COLORS.gray300,
    paddingTop: 8,
  },
  pageFooterText: {
    fontSize: 8,
    color: COLORS.gray600,
  },
})
