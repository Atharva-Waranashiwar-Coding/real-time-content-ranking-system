export const PRODUCT_NAME = "Atlas Learning";
export const PRODUCT_SUBTITLE = "Personalized Technical Learning";
export const PRODUCT_META_DESCRIPTION =
  "Atlas Learning is a personalized technical learning platform powered by a distributed real-time content ranking system.";

export function formatPageTitle(section: string): string {
  return `${section} | ${PRODUCT_NAME}`;
}
