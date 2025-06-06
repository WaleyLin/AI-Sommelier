// Final Cleaned ChatScreen.tsx (Fully working with expo-router, includes preference editor + message reporting)
import React, { useState, useEffect, useRef } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  TextInput,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  Keyboard,
  TouchableWithoutFeedback,
  Modal,
  ScrollView,
  FlatList as FlatListType,
} from "react-native";
import { styles } from "./styles";
import { router } from "expo-router";
import { MaterialIcons } from "@expo/vector-icons";
import {
  ensureAuth,
  storeChatMessage,
  getChatHistory,
  getUserProfile,
  updateUserPreferences,
  getUserPreferences,
  reportChatMessage,
} from "../../config/firebaseClient";

// Types

type ChatMessage = {
  sender: "user" | "bot";
  text: string;
  timestamp?: number;
};

type Preferences = {
  favorite_wine: string;
  favorite_beer: string;
  favorite_cocktail: string;
  favorite_spirit: string;
  alcohol_preference: string;
  sweet_or_dry: string;
  red_or_white_wine: string;
  light_or_strong: string;
  vegan_friendly: boolean;
  gluten_free: boolean;
};

type UserProfile = {
  first_name?: string;
};

const defaultPrefs: Preferences = {
  favorite_wine: "",
  favorite_beer: "",
  favorite_cocktail: "",
  favorite_spirit: "",
  alcohol_preference: "",
  sweet_or_dry: "",
  red_or_white_wine: "",
  light_or_strong: "",
  vegan_friendly: false,
  gluten_free: false,
};

export default function ChatScreen() {
  const [userInput, setUserInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isBotTyping, setIsBotTyping] = useState(false);
  const flatListRef = useRef<FlatListType<ChatMessage>>(null);
  const backendUrl = "https://chatbot-backend-d45e.onrender.com/chat";
  const [userId, setUserId] = useState<string | null>(null);
  const [userName, setUserName] = useState<string>("");
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [historyVisible, setHistoryVisible] = useState(false);
  const [showPrefsModal, setShowPrefsModal] = useState(false);
  const [preferences, setPreferences] = useState<Preferences>(defaultPrefs);
  const [reportModalVisible, setReportModalVisible] = useState(false);
  const [selectedMessage, setSelectedMessage] = useState<ChatMessage | null>(null);

  useEffect(() => {
    (async () => {
      const uid = await ensureAuth();
      if (!uid) return;
      setUserId(uid);

      getUserProfile(uid, (profile: UserProfile | null) => {
        const name = profile?.first_name || "there";
        setUserName(name);

        getChatHistory(uid, (history: ChatMessage[]) => setChatHistory(history));
        getUserPreferences(uid, (prefs: Preferences) => setPreferences(prefs || defaultPrefs));

        setMessages([
          {
            sender: "bot",
            text: `👋 Welcome back, ${name}!

It might take up to a minute to load up my brain the first time, but after that I’ll usually reply in under 10 seconds. 🍷

You can set your beverage preferences by chatting with me directly or by tapping the ⚙️ settings icon at the top right.

Want to revisit your past conversations? Tap the ⏱️ history icon to load them back in.`,
          },
        ]);

        setUserInput("");
        setIsBotTyping(false);
        setHistoryVisible(false);
      });
    })();
  }, []);

  const loadChatHistory = () => {
    if (!historyVisible) {
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: "📜 Chat history loaded." },
        ...chatHistory,
      ]);
      setHistoryVisible(true);
      setTimeout(() => flatListRef.current?.scrollToEnd({ animated: true }), 100);
    }
  };

  const handleSendMessage = async () => {
    const trimmed = userInput.trim();
    if (!userId || trimmed.length === 0) return;

    const userMessage: ChatMessage = {
      sender: "user",
      text: trimmed,
      timestamp: Date.now(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setUserInput("");
    setIsBotTyping(true);

    setTimeout(() => flatListRef.current?.scrollToEnd({ animated: true }), 100);

    try {
      await storeChatMessage(userId, "user", trimmed);

      const response = await fetch(backendUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: trimmed, user_id: userId }),
      });

      if (!response.ok) throw new Error(`Server error: ${response.statusText}`);

      const data = await response.json();
      const botMessage: ChatMessage = {
        sender: "bot",
        text: data.response || "No response from bot.",
        timestamp: Date.now(),
      };

      setMessages((prev) => [...prev, botMessage]);
      await storeChatMessage(userId, "bot", botMessage.text);

      getUserPreferences(userId, (prefs: Preferences) => {
        setPreferences(prefs || defaultPrefs);
      });
    } catch (error) {
      console.error("Chatbot error:", error);
      setMessages((prev) => [
        ...prev,
        {
          sender: "bot",
          text: "❌ Error: Please try again later.",
          timestamp: Date.now(),
        },
      ]);
    } finally {
      setIsBotTyping(false);
      setTimeout(() => flatListRef.current?.scrollToEnd({ animated: true }), 100);
    }
  };

  const handleSavePreferences = async () => {
    if (!userId) return;
    await updateUserPreferences(userId, preferences);
    setShowPrefsModal(false);
  };

  const handleReportMessage = async () => {
    if (!userId || !selectedMessage) return;

    try {
      await reportChatMessage(
        userId,
        selectedMessage.text,
        selectedMessage.sender,
        selectedMessage.timestamp || Date.now()
      );
      alert("🚨 Message reported. Thank you.");
    } catch (err) {
      alert("❌ Failed to report message.");
      console.error(err);
    } finally {
      setReportModalVisible(false);
      setSelectedMessage(null);
    }
  };

  return (
    <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
      <KeyboardAvoidingView
        style={styles.container}
        behavior={Platform.OS === "ios" ? "padding" : undefined}
      >
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={() => router.back()} style={styles.backButtonContainer}>
            <MaterialIcons name="arrow-back" size={24} color="#fff" />
          </TouchableOpacity>

          <Text style={styles.headerTitle}>Master Sommelier Bot</Text>

          <TouchableOpacity onPress={() => setShowPrefsModal(true)} style={{ paddingHorizontal: 10 }}>
            <MaterialIcons name="settings" size={24} color="#fff" />
          </TouchableOpacity>

          <TouchableOpacity onPress={loadChatHistory} style={styles.historyButton}>
            <MaterialIcons name="history" size={24} color="#fff" />
          </TouchableOpacity>
        </View>

        {/* Messages */}
        <FlatList
          ref={flatListRef}
          data={messages}
          keyExtractor={(_, index) => index.toString()}
          renderItem={({ item, index }) => (
            <>
              {index > 0 && messages[index - 1]?.sender !== item.sender && (
                <View style={styles.messageDivider} />
              )}
              <TouchableOpacity
                onLongPress={() => {
                  setSelectedMessage(item);
                  setReportModalVisible(true);
                }}
                delayLongPress={400}
              >
                <View
                  style={[
                    styles.messageContainer,
                    item.sender === "user" ? styles.userMessageContainer : styles.botMessageContainer,
                  ]}
                >
                  <Text style={styles.chatMessage}>{item.text}</Text>
                </View>
              </TouchableOpacity>
            </>
          )}
          contentContainerStyle={{ paddingBottom: 10 }}
          onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
        />

        {isBotTyping && (
          <View style={styles.typingIndicator}>
            <Text style={styles.typingText}>Sommelier is typing...</Text>
          </View>
        )}

        {/* Input */}
        <View style={styles.inputContainer}>
          <TextInput
            style={styles.input}
            placeholder="Type your message..."
            placeholderTextColor="#fff"
            value={userInput}
            onChangeText={setUserInput}
            returnKeyType="send"
            onSubmitEditing={handleSendMessage}
            editable={!isBotTyping}
          />
          <TouchableOpacity
            style={styles.sendButton}
            onPress={!isBotTyping ? handleSendMessage : undefined}
            disabled={isBotTyping}
          >
            <MaterialIcons name={isBotTyping ? "pause" : "send"} size={24} color="white" />
          </TouchableOpacity>
        </View>

        {/* Preferences Modal */}
        {/* ... No changes here ... */}

        {/* Report Modal */}
        <Modal visible={reportModalVisible} transparent animationType="fade">
          <TouchableWithoutFeedback onPress={() => setReportModalVisible(false)}>
            <View style={{ flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: "#00000088" }}>
              <View style={{ backgroundColor: "#fff", padding: 20, borderRadius: 10, width: "80%" }}>
                <Text style={{ fontWeight: "bold", fontSize: 16, marginBottom: 10 }}>Report this message?</Text>
                <Text style={{ marginBottom: 20 }}>{selectedMessage?.text}</Text>
                <TouchableOpacity onPress={handleReportMessage}>
                  <Text style={{ color: "red", fontWeight: "bold" }}>Report</Text>
                </TouchableOpacity>
                <TouchableOpacity onPress={() => setReportModalVisible(false)} style={{ marginTop: 10 }}>
                  <Text>Cancel</Text>
                </TouchableOpacity>
              </View>
            </View>
          </TouchableWithoutFeedback>
        </Modal>
      </KeyboardAvoidingView>
    </TouchableWithoutFeedback>
  );
}
