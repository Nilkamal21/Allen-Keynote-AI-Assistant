import React, { useState } from 'react';
import {
  StyleSheet,
  Text,
  View,
  TextInput,
  TouchableOpacity,
  FlatList,
  ActivityIndicator,
  SafeAreaView,
  StatusBar,
  Alert
} from 'react-native';

// API BASE URL - Replace with your backend server URL or IP address (e.g. http://192.168.1.5:8000)
const API_BASE_URL = 'http://127.0.0.1:8000';

export default function AllenKeynotesScreen() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const searchBook = async (searchQuery) => {
    const targetQuery = searchQuery || query;
    if (!targetQuery.trim()) {
      Alert.alert('Empty Query', 'Please enter a symptom or remedy to search.');
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: targetQuery.trim() }),
      });

      if (!response.ok) {
        throw new Error('Server returned an error.');
      }

      const data = await response.json();
      setResult(data);
    } catch (error) {
      Alert.alert('Search Failed', error.message || 'Unable to connect to server.');
    } finally {
      setLoading(false);
    }
  };

  const renderRemedyCard = ({ item }) => (
    <View style={styles.card}>
      {/* Remedy Header */}
      <View style={styles.cardHeader}>
        <View style={styles.remedyTitleContainer}>
          <Text style={styles.remedyName}>{item.remedy_name}</Text>
          {item.common_name ? (
            <Text style={styles.commonName}>{item.common_name}</Text>
          ) : null}
        </View>
        <View style={styles.pageBadge}>
          <Text style={styles.pageBadgeText}>Page {item.page_number}</Text>
        </View>
      </View>

      {/* Sections & Symptoms */}
      {item.sections.map((sec, secIdx) => (
        <View key={secIdx} style={styles.sectionContainer}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>[ {sec.system_name} ]</Text>
            <Text style={styles.sectionPage}>Page {sec.page_number}</Text>
          </View>
          {sec.symptoms.map((sym, symIdx) => (
            <View key={symIdx} style={styles.symptomRow}>
              <Text style={styles.bullet}>•</Text>
              <Text style={styles.symptomText}>{sym}</Text>
            </View>
          ))}
        </View>
      ))}
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor="#ffffff" />
      
      {/* Top Navbar */}
      <View style={styles.header}>
        <View>
          <Text style={styles.headerTitle}>Allen's Keynotes AI</Text>
          <Text style={styles.headerSubtitle}>Homeopathic Reference Assistant</Text>
        </View>
        
        {result && (
          <View style={[styles.modeBadge, result.mode === 'online' ? styles.onlineBadge : styles.offlineBadge]}>
            <Text style={[styles.modeBadgeText, result.mode === 'online' ? styles.onlineBadgeText : styles.offlineBadgeText]}>
              {result.mode === 'online' ? '🟢 Online AI' : '⚡ Offline Local'}
            </Text>
          </View>
        )}
      </View>

      {/* Search Box */}
      <View style={styles.searchBox}>
        <TextInput
          style={styles.input}
          placeholder="Ask anything (e.g. Nux Vomica or burning stomach pain)..."
          placeholderTextColor="#94a3b8"
          value={query}
          onChangeText={setQuery}
          multiline
        />

        {/* Quick Chips */}
        <View style={styles.chipContainer}>
          <TouchableOpacity
            style={styles.chip}
            onPress={() => {
              setQuery('Nux Vomica stomach symptoms');
              searchBook('Nux Vomica stomach symptoms');
            }}>
            <Text style={styles.chipText}>Nux Vomica</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.chip}
            onPress={() => {
              setQuery('Burning stomach pain with nausea');
              searchBook('Burning stomach pain with nausea');
            }}>
            <Text style={styles.chipText}>Stomach Pain</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.chip}
            onPress={() => {
              setQuery('Headache worse in sunlight');
              searchBook('Headache worse in sunlight');
            }}>
            <Text style={styles.chipText}>Sun Headache</Text>
          </TouchableOpacity>
        </View>

        <TouchableOpacity
          style={styles.searchButton}
          onPress={() => searchBook()}
          disabled={loading}>
          <Text style={styles.searchButtonText}>
            {loading ? 'Searching Book...' : 'Search Allen\'s Keynotes'}
          </Text>
        </TouchableOpacity>
      </View>

      {/* Loading Indicator */}
      {loading && (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#059669" />
          <Text style={styles.loadingText}>Cross-referencing remedies and page numbers...</Text>
        </View>
      )}

      {/* Search Results */}
      {result && (
        <FlatList
          data={result.remedies}
          keyExtractor={(item, idx) => `${item.remedy_name}_${idx}`}
          renderItem={renderRemedyCard}
          contentContainerStyle={styles.listContainer}
          ListHeaderComponent={() => (
            <View>
              {result.ai_synthesis ? (
                <View style={styles.aiBox}>
                  <Text style={styles.aiTitle}>✨ AI Clinical Summary</Text>
                  <Text style={styles.aiText}>{result.ai_synthesis}</Text>
                </View>
              ) : null}
              <Text style={styles.summaryText}>{result.summary}</Text>
            </View>
          )}
          ListFooterComponent={() => (
            <View style={styles.disclaimerBox}>
              <Text style={styles.disclaimerText}>{result.disclaimer}</Text>
            </View>
          )}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  header: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: '#0f172a',
  },
  headerSubtitle: {
    fontSize: 11,
    color: '#64748b',
    fontWeight: '500',
  },
  modeBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    borderWidth: 1,
  },
  onlineBadge: {
    backgroundColor: '#ecfdf5',
    borderColor: '#a7f3d0',
  },
  offlineBadge: {
    backgroundColor: '#fffbeb',
    borderColor: '#fde68a',
  },
  modeBadgeText: {
    fontSize: 11,
    fontWeight: '700',
  },
  onlineBadgeText: {
    color: '#047857',
  },
  offlineBadgeText: {
    color: '#b45309',
  },
  searchBox: {
    backgroundColor: '#ffffff',
    margin: 16,
    padding: 14,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  input: {
    backgroundColor: '#f8fafc',
    borderRadius: 12,
    padding: 12,
    fontSize: 14,
    color: '#0f172a',
    minHeight: 50,
    textAlignVertical: 'top',
    borderWidth: 1,
    borderColor: '#cbd5e1',
  },
  chipContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 10,
  },
  chip: {
    backgroundColor: '#f1f5f9',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
  },
  chipText: {
    fontSize: 12,
    color: '#334155',
    fontWeight: '600',
  },
  searchButton: {
    backgroundColor: '#059669',
    paddingVertical: 12,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 12,
  },
  searchButtonText: {
    color: '#ffffff',
    fontWeight: '700',
    fontSize: 14,
  },
  loadingContainer: {
    alignItems: 'center',
    paddingVertical: 20,
  },
  loadingText: {
    marginTop: 10,
    fontSize: 13,
    color: '#64748b',
  },
  listContainer: {
    paddingHorizontal: 16,
    paddingBottom: 30,
  },
  aiBox: {
    backgroundColor: '#ecfdf5',
    borderColor: '#a7f3d0',
    borderWidth: 1,
    borderRadius: 14,
    padding: 14,
    marginBottom: 14,
  },
  aiTitle: {
    fontSize: 13,
    fontWeight: '800',
    color: '#047857',
    marginBottom: 6,
  },
  aiText: {
    fontSize: 13,
    color: '#1e293b',
    lineHeight: 18,
  },
  summaryText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#475569',
    marginBottom: 12,
  },
  card: {
    backgroundColor: '#ffffff',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  remedyTitleContainer: {
    flex: 1,
    paddingRight: 8,
  },
  remedyName: {
    fontSize: 16,
    fontWeight: '700',
    color: '#0f172a',
  },
  commonName: {
    fontSize: 12,
    color: '#64748b',
    fontStyle: 'italic',
  },
  pageBadge: {
    backgroundColor: '#f1f5f9',
    borderColor: '#cbd5e1',
    borderWidth: 1,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  pageBadgeText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#334155',
  },
  sectionContainer: {
    marginTop: 10,
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: '#f1f5f9',
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  sectionTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: '#065f46',
  },
  sectionPage: {
    fontSize: 11,
    color: '#94a3b8',
  },
  symptomRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 4,
  },
  bullet: {
    fontSize: 14,
    color: '#10b981',
    marginRight: 6,
    lineHeight: 18,
  },
  symptomText: {
    flex: 1,
    fontSize: 13,
    color: '#334155',
    lineHeight: 18,
  },
  disclaimerBox: {
    backgroundColor: '#fffbeb',
    borderColor: '#fde68a',
    borderWidth: 1,
    borderRadius: 12,
    padding: 12,
    marginTop: 12,
  },
  disclaimerText: {
    fontSize: 11,
    color: '#92400e',
    textAlign: 'center',
  },
});
