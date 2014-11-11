<xsl:stylesheet version='1.0' xmlns:xsl='http://www.w3.org/1999/XSL/Transform' xmlns:ns="urn:hl7-org:v3">
	<xsl:output method="xml" encoding="utf-8" indent="yes"/>
	
	<xsl:template match="@*|node()">
		<xsl:copy>
			<xsl:apply-templates select="@*|node()"/>
		</xsl:copy>
	</xsl:template>
	
	<xsl:template match="*//ns:content">
		<content>
			<xsl:attribute name="ID">
				<xsl:call-template name="entryNumbers">
					<xsl:with-param name="entryText">entry_</xsl:with-param>
					<xsl:with-param name="entryNumber"><xsl:number level="any"/></xsl:with-param>
				</xsl:call-template>
			</xsl:attribute>
			<xsl:apply-templates/>
		</content>
	</xsl:template>
	
	<xsl:template name="entryNumbers">
		<xsl:param name="entryText"/>
		<xsl:param name="entryNumber"/>
		<xsl:value-of select="$entryText"/><xsl:value-of select="$entryNumber"/>
	</xsl:template>
</xsl:stylesheet>