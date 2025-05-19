'use client'

import { useState, useEffect } from 'react'
import { ComputerDesktopIcon, ArrowPathIcon } from '@heroicons/react/24/outline'
import { supabase } from '@/utils/supabase/client'
import type { CyberdeskInstance } from '../../types/database'

export function VMInstancesManager() {
  const [vmInstances, setVMInstances] = useState<CyberdeskInstance[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [now, setNow] = useState(new Date())

  // Update current time every second for the running timer
  useEffect(() => {
    const timer = setInterval(() => {
      setNow(new Date())
    }, 1000)
    
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    fetchVMInstances()
  }, [])
  
  const fetchVMInstances = async (isRefresh = false) => {
    if (isRefresh) {
      setIsRefreshing(true)
    } else {
      setIsLoading(true)
    }
    setError(null)
    try {
      // Get the current user session
      const { data, error } = await supabase.auth.getSession()
      
      if (error || !data.session) {
        console.error('Authentication error:', error)
        setError('Authentication error. Please sign in again.')
        setIsLoading(false)
        return
      }
      
      const userId = data.session.user.id
      
      // Fetch VM instances for this user
      const { data: instances, error: fetchError } = await supabase
        .from('cyberdesk_instances')
        .select('*')
        .eq('user_id', userId)
        .order('created_at', { ascending: false })
      
      if (fetchError) {
        throw new Error(fetchError.message)
      }
      
      setVMInstances(instances || [])
    } catch (err) {
      console.error('Error fetching VM instances:', err)
      setError('Failed to load your VM instances. Please try again.')
    } finally {
      setIsLoading(false)
      setIsRefreshing(false)
    }
  }

  // Format the duration as HH:MM:SS
  const formatDuration = (startTime: string) => {
    // Parse the UTC timestamp
    const start = new Date(startTime)
    const utcStart = new Date(start.getTime() - start.getTimezoneOffset() * 60 * 1000)
    // Calculate duration in seconds
    const diff = Math.floor((now.getTime() - utcStart.getTime()) / 1000)
    
    const hours = Math.floor(diff / 3600)
    const minutes = Math.floor((diff % 3600) / 60)
    const seconds = diff % 60
    
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
  }

  // Format date for display - explicitly convert UTC to local time
  const formatDate = (dateString: string) => {
    try {
      // Parse the ISO string into a Date object
      const utcDate = new Date(dateString)
      const date = new Date(utcDate.getTime() - utcDate.getTimezoneOffset() * 60 * 1000)
      
      // Format the date in local time with a consistent format without timezone
      return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        second: '2-digit',
        hour12: true
      })
    } catch (error) {
      console.error('Error formatting date:', error)
      return 'Invalid date'
    }
  }

  // Check if VM is still running (use status field)
  const isVMRunning = (instance: CyberdeskInstance) => {
    return instance.status === 'running' || instance.status === 'pending';
  }
  
  // Get the terminated time (use timeout_at if status is terminated or error)
  const getTerminatedTime = (instance: CyberdeskInstance) => {
    if (instance.status === 'terminated' || instance.status === 'error') {
      return formatDate(instance.timeout_at)
    }
    const running = isVMRunning(instance)
    if (running) return '-'
    // fallback: show timeout_at
    return formatDate(instance.timeout_at)
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      <div className="px-6 py-5 border-b border-gray-200 bg-gray-50 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <ComputerDesktopIcon className="h-5 w-5 text-gray-500" />
          <h3 className="text-base font-medium text-gray-900">Your VM Instances</h3>
        </div>
        <div className="flex items-center space-x-4">
          <div className="text-sm text-gray-500">
            View your virtual machine usage history
          </div>
          <button
            onClick={() => fetchVMInstances(true)}
            disabled={isRefreshing}
            className="p-2 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors"
            title="Refresh VM instances"
          >
            <ArrowPathIcon 
              className={`h-5 w-5 text-gray-500 ${isRefreshing ? 'animate-spin' : ''}`} 
              aria-hidden="true" 
            />
          </button>
        </div>
      </div>
      
      <div className="px-6 py-5">
        {isLoading ? (
          <div className="flex items-center justify-center py-6">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-900"></div>
          </div>
        ) : error ? (
          <div className="text-red-500 py-2">{error}</div>
        ) : vmInstances.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    VM ID
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Terminated
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {vmInstances.map((instance) => {
                  const running = isVMRunning(instance)
                  return (
                    <tr key={instance.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {instance.id}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {running ? (
                          <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                            Running ({formatDuration(instance.created_at)}) 
                          </span>
                        ) : (
                          <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800">
                            Terminated
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDate(instance.created_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {getTerminatedTime(instance)}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-6">
            <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3 mb-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <ComputerDesktopIcon className="h-5 w-5 text-yellow-400" aria-hidden="true" />
                </div>
                <div className="ml-3">
                  <h3 className="text-start text-sm font-medium text-yellow-800">No VM Instances Found</h3>
                  <div className="mt-2 text-sm text-yellow-700">
                    <p>You have not launched any VMs yet.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
