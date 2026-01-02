# --- FILE: schema/sitemap_schema.py (NEW) ---

from pydantic import BaseModel, Field
from typing import List, Optional, Literal

# The choices for page type and placement are defined by Literal
PageType = Literal["Main Page", "Collection Page", "Product Page"]
PlacementType = Literal["Header", "Footer", "Utility", "Hidden"]

# Forward declaration for recursive definition
class SitemapPage(BaseModel):
    name: str = Field(..., description="The unique name of the page (e.g., 'Contact Us', 'Our Products').")
    type: PageType = Field(..., description="The type of content on the page (Main Page, Collection Page, or Product Page).")
    placement: List[PlacementType] = Field(..., description="Where the page link appears (e.g., ['Header', 'Footer']).")
    description: Optional[str] = Field(None, description="A brief summary of the page content, or null.")
    sections: List[str] = Field(..., description="A list of content sections or features on this page (e.g., 'Hero Banner', 'Product Grid').")
    
    # Recursive field for sub-pages. Must be omitted if empty.
    sub_pages: Optional[List["SitemapPage"]] = Field(None, description="A list of sub-pages nested under this page, or null if none.")

# The root sitemap object
class Sitemap(BaseModel):
    site: str = Field(..., description="The name of the client or site (e.g., 'BUBBI').")
    pages: List[SitemapPage] = Field(..., description="The main list of top-level pages for the site.")

# Pydantic utility to allow recursive models to be defined correctly
SitemapPage.model_rebuild()
