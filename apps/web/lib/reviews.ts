export type AccountReview = {
  id: string; display_name: string; anonymous: boolean; rating: number; comment: string;
  created_at: string; updated_at: string; visibility: "VISIBLE" | "HIDDEN" | "WITHDRAWN";
};

export type ReviewState = {
  eligible: boolean; email_verified: boolean; account_display_name: string; review: AccountReview | null;
};
