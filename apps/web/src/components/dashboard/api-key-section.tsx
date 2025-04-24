'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/button'
import { CheckIcon, ClipboardIcon, KeyIcon } from '@heroicons/react/24/outline'
import { ArrowPathIcon } from '@heroicons/react/24/outline'

interface ApiKeyData {
  key: string
  keyId: string
}

export function ApiKeySection() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [identityExists, setIdentityExists] = useState(false)
  const [apiKey, setApiKey] = useState<ApiKeyData | null>(null)
  const [copied, setCopied] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  // Toast notification function
  const showToast = (message: string, type: 'success' | 'error' = 'success') => {
    // In a real implementation, this would use a toast library
    console.log(`Toast (${type}):`, message)
  }

  useEffect(() => {
    checkIdentity()
  }, [])

  const checkIdentity = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await fetch('/api/unkey')
      
      if (!response.ok) {
        throw new Error('Failed to check identity')
      }
      
      const data = await response.json()
      
      setIdentityExists(data.exists)
      
      if (data.exists && data.keys && data.keys.length > 0) {
        // Sort keys by creation date and get the most recent one
        const sortedKeys = [...data.keys].sort((a, b) => {
          return new Date(b.meta?.createdAt || 0).getTime() - 
                 new Date(a.meta?.createdAt || 0).getTime()
        })
        
        setApiKey({
          key: sortedKeys[0].key,
          keyId: sortedKeys[0].id
        })
      }
    } catch (err) {
      console.error('Error checking identity:', err)
      setError('Failed to check your API key status')
    } finally {
      setLoading(false)
    }
  }

  const createApiKey = async () => {
    setIsCreating(true)
    setError(null)
    
    try {
      const response = await fetch('/api/unkey', {
        method: 'POST'
      })
      
      if (!response.ok) {
        throw new Error('Failed to create API key')
      }
      
      const data = await response.json()
      
      setIdentityExists(true)
      setApiKey({
        key: data.key,
        keyId: data.keyId
      })
      
      showToast("Your new API key has been generated successfully.", "success")
    } catch (err) {
      console.error('Error creating API key:', err)
      setError('Failed to create your API key')
      
      showToast("Failed to create your API key. Please try again.", "error")
    } finally {
      setIsCreating(false)
    }
  }

  const copyToClipboard = () => {
    if (apiKey?.key) {
      navigator.clipboard.writeText(apiKey.key)
      setCopied(true)
      
      showToast("API key copied to clipboard", "success")
      
      setTimeout(() => setCopied(false), 2000)
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="p-6 animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-3/4 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2 mb-6"></div>
          <div className="h-10 bg-gray-200 rounded w-full mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-6"></div>
          <div className="h-10 bg-gray-200 rounded w-full"></div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-red-200 overflow-hidden">
        <div className="px-6 py-5 border-b border-gray-200 bg-gray-50">
          <div className="flex items-center gap-2">
            <KeyIcon className="h-5 w-5" />
            <h3 className="text-lg font-medium text-gray-900">API Key</h3>
          </div>
          <p className="text-sm text-gray-500 mt-1">
            There was a problem loading your API key information
          </p>
        </div>
        <div className="px-6 py-5">
          <p className="text-red-500">{error}</p>
        </div>
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
          <Button onClick={checkIdentity} variant="outline" className="w-full">
            Try Again
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      <div className="px-6 py-5 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center gap-2">
          <KeyIcon className="h-5 w-5 text-gray-500" />
          <h3 className="text-lg font-medium text-gray-900">API Key</h3>
        </div>
        <p className="text-sm text-gray-500 mt-1">
          {identityExists 
            ? "Use this key to authenticate API requests to our service" 
            : "Generate an API key to start using our service"}
        </p>
      </div>
      <div className="px-6 py-5">
        {identityExists && apiKey ? (
          <div className="space-y-4">
            <div className="flex items-center">
              <div className="flex-1 bg-gray-100 rounded-md px-4 py-3 font-mono text-sm text-gray-800 truncate">
                {apiKey.key}
              </div>
              <button
                onClick={copyToClipboard}
                className="ml-3 p-2 rounded-md hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                title="Copy to clipboard"
              >
                {copied ? (
                  <CheckIcon className="h-5 w-5 text-green-500" />
                ) : (
                  <ClipboardIcon className="h-5 w-5 text-gray-500" />
                )}
              </button>
            </div>
            <div className="text-sm text-gray-500">
              Keep this key secure. Never share it in client-side code or public repositories.
            </div>
          </div>
        ) : (
          <div className="text-center py-6">
            <p className="text-gray-500 mb-4">You don&apos;t have an API key yet</p>
          </div>
        )}
      </div>
      <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
        <Button
          onClick={createApiKey}
          disabled={isCreating}
          className="w-full"
          variant={identityExists ? "outline" : "primary"}
        >
          {isCreating ? (
            <>
              <ArrowPathIcon className="h-4 w-4 mr-2 animate-spin" />
              {identityExists ? "Regenerating..." : "Generating..."}
            </>
          ) : identityExists ? (
            "Regenerate API Key"
          ) : (
            "Generate API Key"
          )}
        </Button>
      </div>
    </div>
  )
}
