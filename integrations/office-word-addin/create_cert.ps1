$cert = New-SelfSignedCertificate -DnsName "localhost", "127.0.0.1" -CertStoreLocation "Cert:\CurrentUser\My" -NotAfter (Get-Date).AddYears(5) -FriendlyName "Office Add-in Localhost" -KeyExportPolicy Exportable -KeyUsage DigitalSignature,KeyEncipherment -Type SSLServerAuthentication
$pwd = ConvertTo-SecureString -String "office" -Force -AsPlainText
$certPath = "$env:USERPROFILE\.office-addin-dev-certs"
Export-PfxCertificate -Cert $cert -FilePath "$certPath\localhost.pfx" -Password $pwd
Export-Certificate -Cert $cert -FilePath "$certPath\localhost_root.crt"
Import-Certificate -FilePath "$certPath\localhost_root.crt" -CertStoreLocation "Cert:\CurrentUser\Root"
Write-Host "Certificate generated and trusted: $($cert.Thumbprint)"
