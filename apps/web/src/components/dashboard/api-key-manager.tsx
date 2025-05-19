'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/button'
import { ClipboardIcon, KeyIcon, ArrowPathIcon } from '@heroicons/react/24/outline'
import { CheckIcon } from '@heroicons/react/24/solid'
import { supabase } from '@/utils/supabase/client'
interface ApiKey {
  id: string
  key: string
  createdAt: string
}

export function ApiKeyManager() {
  const [apiKey, setApiKey] = useState<ApiKey | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const [keyExists, setKeyExists] = useState(false)

  useEffect(() => {
    fetchApiKey()
  }, [])
  
  const fetchApiKey = async () => {
    setIsLoading(true)
    setError(null)
    try {
      // Get the current user session
      const { data, error } = await supabase.auth.getSession();
      
      if (error || !data.session) {
        console.error('Authentication error:', error)
        setError('Authentication error. Please sign in again.')
        setIsLoading(false)
        return
      }
      
      const userId = data.session.user.id
      console.log('Checking if API key exists for user:', userId)
      
      // Call our API endpoint with the userId as a query parameter
      const response = await fetch(`/api/unkey?userId=${userId}`, {
        method: 'GET',
      })
      
      console.log('API response status:', response.status)
      const responseData = await response.json()
      
      if (!response.ok) {
        throw new Error(responseData.error || 'Failed to fetch API key')
      }
      
      console.log('API key check response:', responseData)
      setKeyExists(responseData.exists)
      
      if (responseData.exists && responseData.key) {
        // We have a key, set it
        setApiKey({
          id: responseData.keyId || 'unknown',
          key: responseData.key,
          createdAt: new Date().toISOString(),
        })
      } else {
        setApiKey(null)
      }
    } catch (err) {
      console.error('Error fetching API key:', err)
      setError('Failed to load your API key. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const generateApiKey = async () => {
    setIsGenerating(true)
    setError(null)
    
    try {
      // Get the current user session
      const { data, error } = await supabase.auth.getSession();
      
      if (error || !data.session) {
        console.error('Authentication error:', error)
        setError('Authentication error. Please sign in again.')
        setIsGenerating(false)
        return
      }
      
      const userId = data.session.user.id
      console.log('Generating API key for user:', userId)
      
      // Call our API endpoint with the userId in the body
      const response = await fetch('/api/unkey', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ userId }),
      })
      
      const responseData = await response.json()
      
      if (!response.ok) {
        throw new Error(responseData.error || 'Failed to generate API key')
      }
      
      if (responseData.key) {
        setApiKey({
          id: responseData.keyId || 'unknown',
          key: responseData.key,
          createdAt: new Date().toISOString(),
        })
        setKeyExists(true)
      } else {
        throw new Error('No key returned from API')
      }
    } catch (err) {
      console.error('Error generating API key:', err)
      setError('Failed to generate a new API key. Please try again.')
    } finally {
      setIsGenerating(false)
    }
  }

  const copyToClipboard = () => {
    if (apiKey) {
      navigator.clipboard.writeText(apiKey.key)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      <div className="px-6 py-5 border-b border-gray-200 bg-gray-50 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <KeyIcon className="h-5 w-5 text-gray-500" />
          <h3 className="text-base font-medium text-gray-900">Your API Key</h3>
        </div>
        <div className="text-sm text-gray-500">
          Use this key to authenticate API requests
        </div>
      </div>
      
      <div className="px-6 py-5">
        {isLoading ? (
          <div className="flex items-center justify-center py-6">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-900"></div>
          </div>
        ) : error ? (
          <div className="text-red-500 py-2">{error}</div>
        ) : apiKey ? (
          <div className="space-y-4">
            <div className="bg-green-50 border border-green-200 rounded-md p-3 mb-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <CheckIcon className="h-5 w-5 text-green-400" aria-hidden="true" />
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-green-800">API Key Active</h3>
                  <div className="mt-2 text-sm text-green-700">
                    <p>You have an active API key that you can use to authenticate your API requests.</p>
                  </div>
                </div>
              </div>
            </div>
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
              Keep this key secret. Do not share it in client-side code.
            </div>
            <div className="text-sm text-gray-600 mt-4">
              <p>This is your current API key. If you&apos;ve lost access to it, you can generate a new one below.</p>
            </div>
          </div>
        ) : keyExists ? (
          <div className="space-y-4">
            <div className="bg-blue-50 border border-blue-200 rounded-md p-3 mb-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <KeyIcon className="h-5 w-5 text-blue-400" aria-hidden="true" />
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-blue-800">API Key Already Created</h3>
                  <div className="mt-2 text-sm text-blue-700">
                    <p>You&apos;ve already created an API key.</p>
                    <p className="mt-1">If you lost your API key, you can generate a new key below, which will replace your existing key.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center py-6">
            <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3 mb-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <KeyIcon className="h-5 w-5 text-yellow-400" aria-hidden="true" />
                </div>
                <div className="ml-3">
                  <h3 className="text-start text-sm font-medium text-yellow-800">No API Key Found</h3>
                  <div className="mt-2 text-sm text-yellow-700">
                    <p>You don&apos;t have an API key yet. Generate one to start using our API.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        <div className="mt-5 flex justify-center">
          <Button
            type="button"
            onClick={generateApiKey}
            disabled={isGenerating}
            className="flex items-center justify-center px-6"
            variant={apiKey || keyExists ? "outline" : "primary"}
          >
            {isGenerating ? (
              <>
                <ArrowPathIcon className="animate-spin -ml-1 mr-2 h-4 w-4" />
                Generating...
              </>
            ) : apiKey ? (
              'Regenerate API Key'
            ) : keyExists ? (
              'Generate New API Key'
            ) : (
              'Generate API Key'
            )}
          </Button>
        </div>
      </div>
    </div>
  )
}
