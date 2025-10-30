import React, { useState, useRef } from 'react';
import { View, Text, ScrollView, Alert, StyleSheet } from 'react-native';

export default function App() {
  const [totalScroll, setTotalScroll] = useState(0);
  const [alertShown, setAlertShown] = useState(false);
  const lastOffsetY = useRef(0);

  const SCROLL_THRESHOLD = 1000; // adjust as needed

  const handleScroll = (event) => {
    const offsetY = event.nativeEvent.contentOffset.y;
    const delta = Math.abs(offsetY - lastOffsetY.current);
    lastOffsetY.current = offsetY;

    // update scroll distance
    setTotalScroll((prev) => {
      const newTotal = prev + delta;

      if (newTotal > SCROLL_THRESHOLD && !alertShown) {
        setAlertShown(true);
        Alert.alert(
          'Take a Break!',
          'You have scrolled a lot. Consider taking a short break.',
          [
            {
              text: 'OK',
              onPress: () => {
                setTotalScroll(0);
                setAlertShown(false);
              },
            },
          ]
        );
      }

      return newTotal;
    });
  };

  return (
    <ScrollView
      style={styles.container}
      onScroll={handleScroll}
      scrollEventThrottle={16}
    >
      {Array.from({ length: 50 }).map((_, i) => (
        <View key={i} style={styles.item}>
          <Text>Item {i + 1}</Text>
        </View>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20 },
  item: {
    height: 100,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 10,
    backgroundColor: '#f0f0f0',
    borderRadius: 10,
  },
});
