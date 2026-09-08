import React, { useEffect, useRef, useState } from "react";
import {
  View,
  Text,
  Pressable,
  TextInput,
  FlatList,
  ActivityIndicator,
} from "react-native";
import { Image } from "expo-image";
import { KeyboardAvoidingView } from "react-native-keyboard-controller";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { PaperPlaneRight, Sparkle } from "phosphor-react-native";

import { makeStyles, useTheme } from "@/src/theme";
import { useI18n } from "@/src/i18n";
import { api } from "@/src/api/client";

type Msg = { id: string; role: "user" | "assistant"; content: string };

const AI_AVATAR =
  "https://images.unsplash.com/photo-1737644467636-6b0053476bb2?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjAzNDR8MHwxfHNlYXJjaHwxfHxmcmllbmRseSUyMGFpJTIwcm9ib3QlMjBhdmF0YXJ8ZW58MHx8fHwxNzg4ODU3NjMwfDA&ixlib=rb-4.1.0&q=85";

export default function Assistant() {
  const styles = useStyles();
  const { colors } = useTheme();
  const insets = useSafeAreaInsets();
  const { t } = useI18n();

  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(true);
  const listRef = useRef<FlatList<Msg>>(null);

  useEffect(() => {
    (async () => {
      try {
        const history = await api.get("/assistant/history");
        setMessages(history);
      } catch {
        // ignore
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const scrollDown = () => {
    setTimeout(() => listRef.current?.scrollToEnd({ animated: true }), 80);
  };

  const send = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || sending) return;
    setInput("");
    const userMsg: Msg = { id: `u-${Date.now()}`, role: "user", content: trimmed };
    setMessages((m) => [...m, userMsg]);
    setSending(true);
    scrollDown();
    try {
      const res = await api.post("/assistant/chat", { message: trimmed });
      const aiMsg: Msg = { id: `a-${Date.now()}`, role: "assistant", content: res.reply };
      setMessages((m) => [...m, aiMsg]);
    } catch {
      const aiMsg: Msg = {
        id: `a-${Date.now()}`,
        role: "assistant",
        content: t("something_wrong"),
      };
      setMessages((m) => [...m, aiMsg]);
    } finally {
      setSending(false);
      scrollDown();
    }
  };

  const suggestions = [t("suggest_1"), t("suggest_2"), t("suggest_3")];

  return (
    <View style={styles.root}>
      <View style={[styles.header, { paddingTop: insets.top + 8 }]}>
        <Image source={{ uri: AI_AVATAR }} style={styles.headerAvatar} contentFit="cover" />
        <View>
          <Text style={styles.headerTitle}>{t("ai_assistant")}</Text>
          <Text style={styles.headerSub}>Arth</Text>
        </View>
      </View>

      <KeyboardAvoidingView
        behavior="translate-with-padding"
        keyboardVerticalOffset={insets.top + 60}
        style={styles.flex}
      >
        {loading ? (
          <View style={styles.center}>
            <ActivityIndicator color={colors.brandPrimary} />
          </View>
        ) : messages.length === 0 ? (
          <View style={styles.emptyWrap}>
            <Image source={{ uri: AI_AVATAR }} style={styles.emptyAvatar} contentFit="cover" />
            <Text style={styles.emptyText}>{t("ai_greeting")}</Text>
            <View style={styles.suggestWrap}>
              {suggestions.map((s, i) => (
                <Pressable key={i} style={styles.suggestChip} onPress={() => send(s)} testID={`suggest-${i}`}>
                  <Sparkle size={15} color={colors.brand} weight="fill" />
                  <Text style={styles.suggestText}>{s}</Text>
                </Pressable>
              ))}
            </View>
          </View>
        ) : (
          <FlatList
            ref={listRef}
            data={messages}
            keyExtractor={(m) => m.id}
            contentContainerStyle={styles.listContent}
            showsVerticalScrollIndicator={false}
            onContentSizeChange={scrollDown}
            renderItem={({ item }) => (
              <View
                style={[styles.bubbleRow, item.role === "user" ? styles.bubbleRowUser : styles.bubbleRowAi]}
              >
                <View
                  style={[styles.bubble, item.role === "user" ? styles.bubbleUser : styles.bubbleAi]}
                  testID={`msg-${item.role}`}
                >
                  <Text style={item.role === "user" ? styles.bubbleTextUser : styles.bubbleTextAi}>
                    {item.content}
                  </Text>
                </View>
              </View>
            )}
            ListFooterComponent={
              sending ? (
                <View style={[styles.bubbleRow, styles.bubbleRowAi]}>
                  <View style={[styles.bubble, styles.bubbleAi]}>
                    <Text style={styles.bubbleTextAi}>{t("thinking")}</Text>
                  </View>
                </View>
              ) : null
            }
          />
        )}

        <View style={[styles.inputBar, { paddingBottom: insets.bottom + 8 }]}>
          <TextInput
            style={styles.input}
            value={input}
            onChangeText={setInput}
            placeholder={t("ask_placeholder")}
            placeholderTextColor={colors.muted}
            multiline
            testID="assistant-input"
          />
          <Pressable
            style={[styles.sendBtn, (!input.trim() || sending) && styles.sendDisabled]}
            onPress={() => send(input)}
            disabled={!input.trim() || sending}
            testID="assistant-send"
          >
            <PaperPlaneRight size={20} color={colors.onBrandPrimary} weight="fill" />
          </Pressable>
        </View>
      </KeyboardAvoidingView>
    </View>
  );
}

const useStyles = makeStyles((colors) => ({
  root: { flex: 1, backgroundColor: colors.surface },
  flex: { flex: 1 },
  header: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    paddingHorizontal: 16,
    paddingBottom: 12,
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.divider,
  },
  headerAvatar: { width: 40, height: 40, borderRadius: 20 },
  headerTitle: { fontSize: 17, fontWeight: "800", color: colors.onSurface },
  headerSub: { fontSize: 12, color: colors.success, fontWeight: "600" },
  center: { flex: 1, alignItems: "center", justifyContent: "center" },
  emptyWrap: { flex: 1, alignItems: "center", justifyContent: "center", padding: 24 },
  emptyAvatar: { width: 88, height: 88, borderRadius: 44, marginBottom: 16 },
  emptyText: { fontSize: 15, color: colors.onSurfaceSecondary, textAlign: "center", lineHeight: 22 },
  suggestWrap: { marginTop: 24, gap: 10, width: "100%" },
  suggestChip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    backgroundColor: colors.surfaceSecondary,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 14,
    paddingHorizontal: 16,
    paddingVertical: 14,
  },
  suggestText: { fontSize: 14, color: colors.onSurface, fontWeight: "600" },
  listContent: { padding: 16, gap: 10 },
  bubbleRow: { flexDirection: "row" },
  bubbleRowUser: { justifyContent: "flex-end" },
  bubbleRowAi: { justifyContent: "flex-start" },
  bubble: { maxWidth: "82%", borderRadius: 18, paddingHorizontal: 14, paddingVertical: 10 },
  bubbleUser: { backgroundColor: colors.brandPrimary, borderBottomRightRadius: 4 },
  bubbleAi: { backgroundColor: colors.surfaceSecondary, borderBottomLeftRadius: 4 },
  bubbleTextUser: { color: colors.onBrandPrimary, fontSize: 15, lineHeight: 21 },
  bubbleTextAi: { color: colors.onSurface, fontSize: 15, lineHeight: 21 },
  inputBar: {
    flexDirection: "row",
    alignItems: "flex-end",
    gap: 10,
    paddingHorizontal: 16,
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: colors.divider,
    backgroundColor: colors.surface,
  },
  input: {
    flex: 1,
    maxHeight: 120,
    minHeight: 44,
    backgroundColor: colors.surfaceSecondary,
    borderRadius: 22,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 15,
    color: colors.onSurface,
  },
  sendBtn: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: colors.brandPrimary,
    alignItems: "center",
    justifyContent: "center",
  },
  sendDisabled: { opacity: 0.5 },
}));
