param([string]$InputDocx,[string]$OutputPdf)
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$word.AutomationSecurity = 3
try {
    $doc = $word.Documents.Open($InputDocx, $false, $false)
    $doc.Fields.Update() | Out-Null
    foreach ($toc in $doc.TablesOfContents) {
        $toc.Update()
        $toc.Range.Font.Name = 'Times New Roman'
        $toc.Range.Font.Size = 10.5
        $toc.Range.ParagraphFormat.LineSpacingRule = 0
        $toc.Range.ParagraphFormat.SpaceBefore = 0
        $toc.Range.ParagraphFormat.SpaceAfter = 1
    }
    $doc.Repaginate()
    $doc.Fields.Update() | Out-Null
    $doc.Save()
    $doc.ExportAsFixedFormat($OutputPdf, 17)
    $doc.Close(0)
    Write-Output "Rendered $OutputPdf"
} finally { $word.Quit() }
